import sys
from logging import exception
import uvicorn
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query
import time
import pandas as pd
import numpy as np
from fastapi_utils.tasks import repeat_every

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportError
transport = AIOHTTPTransport(
    url="https://api.thegraph.com/subgraphs/name/balancer-labs/balancer"
)

# CORS
origins = [
    "http://localhost:8080",
    "localhost:8080",
    "https://onlyc.github.io/balancer-chart/",
    "https://onlyc.github.io"
]

# # =============================================
# # Configure logging
# tools.createLogger(__name__)


# # =============================================
# # set up threading pool
# __threads__ = tools.read_single_argv("--threads")
# __threads__ = int(__threads__) if tools.is_number(__threads__) else None
# asynctools.multitasking.createPool(__name__, __threads__)

api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Declare global variables
pools = pd.DataFrame()
bars = {}


# Caching pools list
@api.on_event("startup")
@repeat_every(seconds=300)
async def run():
    # Using `async with` on the client will start a connection on the transport
    # and provide a `session` variable to execute queries on this connection
    tempPools = []
    foundPools = []
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        while len(tempPools) < 1 or len(foundPools) > 0:
            query = gql(
                """
                query getPools ($skip: Int!) {
                    pools (where: { liquidity_gt: 0 }, first: 1000, skip: $skip, orderBy: liquidity, orderDirection: desc ){
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
            params = {
                "skip": len(tempPools)
            }
            try:
                # Execute single query
                result = await session.execute(query, variable_values=params)
                foundPools = result["pools"]
                tempPools = tempPools + foundPools
            except:
                print('TheGraph problem. Wait 60s before restart...')
                time.sleep(60)
                # sys.exit()

        # Filter pools have 2 tokens
        tempPools = [x for x in tempPools if len(x["tokens"]) == 2]
        # Format data
        tempPools = list(
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
                tempPools
            )
        )
        # convert to Dataframe
        global pools
        pools = pd.DataFrame(tempPools)


# Datetime index to epoch number
def datetime_to_unix(dt):
    temp = dt.copy()
    temp.index = temp.index.astype("int64") // 10 ** 6
    temp.dropna(inplace=True)
    return temp


@api.get("/pools")
async def api_get_pools():
    """ Return list of pools. """
    return pools.reset_index(drop=True).to_dict('records')


@api.get("/chart/{poolid}")
async def api_get_chart(poolid: str, timeframe: str = Query("1H", regex="^(15T|1H|4H|1D|1W)$", min_length=2, max_length=3), baseSwitch: Optional[int] = Query(0, gt=-1, lt=2), before: Optional[int] = Query(None, gt=time.time()-30000000000, lt=time.time()*1000)):
    """ Read the bars. """
    try:
        metadata = pools.loc[pools["id"] == poolid].reset_index(
            drop=True).to_dict('records')[0]
    except:
        return {"error": "Not found"}
    if baseSwitch == 1:
        quote = metadata["quote"]
        metadata["quote"] = metadata["base"]
        metadata["base"] = quote

    data = await getData(metadata, timeframe, before)
    if isinstance(data, pd.DataFrame):
        data = datetime_to_unix(data)
        bars = data[['price', 'value']]
        liquidity = data['liquidity']
        return {'bars': bars.reset_index().values.tolist(), 'liquidity': liquidity.reset_index().values.tolist(), "metadata": metadata}
    else:
        return data


# Get & resample swaps data from thegraph.
async def getData(pool, timeframe, before=None):
    def tfEpoch(i):
        switcher = {
            '15T': 900,
            '1H': 3600,
            '4H': 14400,
            '1D': 86400,
            '1W': 604800
        }
        return switcher.get(i, 86400)

    def tfMultiplier(i):
        switcher = {
            '15T': 64,
            '1H': 32,
            '4H': 16,
            '1D': 16,
            '1W': 10
        }
        return switcher.get(i, 16)
    swaps = []
    before = int(before/1000 if before else time.time())
    after = before - tfEpoch(timeframe)*tfMultiplier(timeframe)
    # Rounded to timeframe, ex: will get data in a whole week, from 0:00 of Monday to 23:59:59 of Sunday. To resample full candle.
    after = after - (after % tfEpoch(timeframe))

    # Using `async with` on the client will start a connection on the transport
    # and provide a `session` variable to execute queries on this connection
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        tempSwaps = []
        try:
            while len(swaps) < 1 or len(tempSwaps) > 0:
                # Execute single query
                query = gql(
                    """
                    query getSwaps($pairid: ID!, $limit: Int!, $before: Int!, $after: Int!) {
                        pools(where: {id : $pairid } ) {
                            swaps(where: {timestamp_lt: $before, timestamp_gte: $after}, first: $limit, orderBy: timestamp, orderDirection: desc) {
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
                    "pairid": pool["id"],
                    # "skip": len(swaps),
                    "limit": 1000,
                    "before": before,
                    "after": after,
                }

                result = await session.execute(query, variable_values=params)
                tempSwaps = result["pools"][0]["swaps"]
                if len(tempSwaps) < 1:
                    break
                swaps = swaps + tempSwaps
                before = swaps[len(swaps)-1]['timestamp']

        except TransportError:
            return 'TheGraph network error. Please try again later!'
        except:
            return 'Unknown error. Please try again later!'
        # convert to Dataframe
        # swaps = swaps.reverse()
        swapsDF = pd.DataFrame(swaps)
        if len(swapsDF.index) < 1:
            return None
        swapsDF = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(swapsDF["timestamp"], unit="s"),
                "in": pd.Series(swapsDF["tokenAmountIn"], dtype="float"),
                "out": pd.Series(swapsDF["tokenAmountOut"], dtype="float"),
                "liquidity": pd.Series(swapsDF["poolLiquidity"], dtype="float"),
                "tokenInSym": pd.Series(swapsDF["tokenInSym"], dtype="string"),
                "tokenOutSym": pd.Series(swapsDF["tokenOutSym"], dtype="string"),
                "value": pd.Series(swapsDF["value"], dtype="float"),
            }
        )
        # Calculate price base on token in symbol (base) vs token out symbol (quote).
        inColumn = np.where(swapsDF["tokenInSym"] ==
                            pool["base"], swapsDF["out"], swapsDF["in"])
        outColumn = np.where(swapsDF["tokenOutSym"] ==
                             pool["quote"], swapsDF["in"], swapsDF["out"])
        swapsDF["in"] = inColumn
        swapsDF["out"] = outColumn
        swapsDF["price"] = swapsDF["in"] / swapsDF["out"]
        swapsDF.set_index("timestamp", drop=True, inplace=True)
        swapsDF = swapsDF.resample(timeframe if timeframe != '1W' else 'W-MON').agg(
            {"price": "ohlc", "value": "sum", "liquidity": "last"})

        return swapsDF


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
