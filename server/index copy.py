from multiprocessing import Process
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from datetime import datetime
import time
import pandas as pd
import numpy as np
import json
from decimal import Decimal
import asyncio
# from . import asynctools, tools

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

transport = AIOHTTPTransport(
    url="https://api.thegraph.com/subgraphs/name/balancer-labs/balancer"
)
# from pydantic import BaseModel
origins = [
    "http://localhost:8080",
]

# # =============================================
# # Configure logging
# tools.createLogger(__name__)


# # =============================================
# # set up threading pool
# __threads__ = tools.read_single_argv("--threads")
# __threads__ = int(__threads__) if tools.is_number(__threads__) else None
# asynctools.multitasking.createPool(__name__, __threads__)


class Server():

    def __init__(self):
        self.pools = []
        self.bars = {}

        # self.threads = asynctools.multitasking.getPool(__name__)['threads']
        self.api = FastAPI()
        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # register endpoints
        self.api.get("/bars/{symbol}")(self.api_get_bars)

    async def run(self):
        # Using `async with` on the client will start a connection on the transport
        # and provide a `session` variable to execute queries on this connection
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:

            # Execute single query
            query = gql(
                """
                query getPools {
                    pools (where: { liquidity_gt: 0 }, first: 100, orderBy: liquidity, orderDirection: desc ){
                        id
                        tokens {
                            name
                            symbol
                        }
                        liquidity
                    }
                }
            """
            )
            result = await session.execute(query)
            # convert to Dataframe
            result = result["pools"]
            # Filter pools have 2 tokens
            pools = [x for x in result if len(x["tokens"]) == 2]
            pools = list(
                map(
                    (
                        lambda x: {
                            "id": x["id"],
                            "liquidity": x["liquidity"],
                            "base": x["tokens"][0]["symbol"],
                            "quote": x["tokens"][1]["symbol"],
                            "baseName": x["tokens"][0]["name"],
                            "quoteName": x["tokens"][1]["name"],
                        }
                    ),
                    pools
                )
            )
            self.pools = pd.DataFrame(pools)
            print(self.pools.head())

            self.proc = Process(target=uvicorn.run,
                                args=[self.api],
                                kwargs={
                                    "host": "0.0.0.0",
                                    "port": 8000},
                                daemon=True)
            self.proc.start()

    # async def close(self):
    #     """ Gracefull shutdown. """
    #     logging.warning("Shutting down the app.")

    def datetime_to_unix(dt):
        temp = dt.copy()
        temp.index = temp.index.astype("int64") // 10 ** 6
        return temp

    async def api_get_bars(self, symbol):
        """ Read the bars. """
        print(symbol)
        print(self.pools.loc[(self.pools["base"] +
              "-" + self.pools["quote"]) == symbol, "id"])
        selected = self.pools.loc[(self.pools["base"] + "-" + self.pools["quote"]) == symbol, "id"].values[
            0
        ]

        return self.datetime_to_unix(await self.getData(selected)).reset_index().values.tolist()

    async def getData(self, id):

        # Using `async with` on the client will start a connection on the transport
        # and provide a `session` variable to execute queries on this connection
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:

            # Execute single query
            query = gql(
                """
                query getSwaps($pairid: ID!, $limit: Int!, $skip: Int!) {
                    pools(where: {id : $pairid } ) {
                        swaps(first: $limit, skip: $skip, orderBy: timestamp, orderDirection: desc) {
                        timestamp
                        tokenAmountIn
                        tokenAmountOut
                        tokenInSym
                        tokenOutSym
                        poolLiquidity
                        value
                        }
                    }
                }
            """
            )
            # Static parameters
            params = {
                "pairid": id,
                "skip": 0,
                "limit": 500,
            }

            result = await session.execute(query, variable_values=params)
            # convert to Dataframe
            swaps = pd.DataFrame(result["pools"][0]["swaps"])
            swaps = pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(swaps["timestamp"], unit="s"),
                    "in": pd.Series(swaps["tokenAmountIn"], dtype="float"),
                    "out": pd.Series(swaps["tokenAmountOut"], dtype="float"),
                    "liquidity": pd.Series(swaps["poolLiquidity"], dtype="float"),
                    "tokenInSym": pd.Series(swaps["tokenInSym"], dtype="string"),
                    "tokenOutSym": pd.Series(swaps["tokenOutSym"], dtype="string"),
                    "value": pd.Series(swaps["value"], dtype="float"),
                }
            )

            # Calculate price base on token in vs token out.
            inColumn = np.where(swaps["tokenInSym"] ==
                                "WETH", swaps["in"], swaps["out"])
            outColumn = np.where(swaps["tokenInSym"] ==
                                 "WETH", swaps["out"], swaps["in"])
            swaps["in"] = inColumn
            swaps["out"] = outColumn
            swaps["price"] = swaps["in"] / swaps["out"]
            swaps.set_index("timestamp", drop=True, inplace=True)

            print(swaps.info())
            print(swaps.head(50))
            swaps = swaps.resample("1h").agg({"price": "ohlc", "value": "sum"})
            print(swaps.head())
            print(len(swaps))

            # Cache processed ohlcv data to memory for faster 1st load
            self.bars["BAL-WETH"] = swaps


if __name__ == "__main__":
    sv = Server()
    uvicorn.run(sv, host="127.0.0.1", port=8000, log_level="info")
