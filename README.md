# Balancer charts

This project is to show volume and price information of trading pairs on balancer protocol, including total liquidity of the pool.  
I'm not a front-end dev so it's not so beautiful :(
DEMO: https://onlyc.github.io/balancer-chart/
![](https://i.imgur.com/Valg2qG.png)

## Getting Started

Run the backend server:

```bash
cd server
pip install -r requirements.txt
python index.py
```

Change to baseURL in /libs/axios.js to backend's address.

Build and deploy the frontend:

```bash
npm i
npm run build
```

## Features

- Timeframes: 15M, 1H, 4H, 1D (default), 1W or many more if needed.
- Liquidity indicator
- Common TA indicators
- Switch base & quote asset
- Chart settings saved to cookies
- Cached pools list for instant search
- Responsive design.

## How to use

- Load chart:
  - Enter symbol or poolID to search bar then select
  - or use url: http://domain/?pool=*PoolID*
- Switch base:
  - Enable it will switch the base & quote of pair. Ex: BAL/WETH to WETH/BAL.
- Indicators:
  - Every indicator has buttons: Add, Remove, Up, Down
  - Click on any + button to add more indicator
  - Can change height of them by dragging horizontal line.

## Future development plans

- Screenshot
- Websocket

  - Pushing new data to the chart in realtime.

- Database

  - I thought about this a lot and finally decided not to do it atm because the load speed is fast enough and I also want to keep this project lightweight & more like a DAPP that use blockchain as database.
  - We still need a caching method in the future when we have more historical data & more traders.

- Code quality
  - Adding more tests for better maintainability
  - Typescript support
