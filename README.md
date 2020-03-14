# ASX-Stock-Monitor
A little program i wrote to monitor the ASX Stocks with Alpha Vantage and some Yahoo trickery

If the market is open it will pull 5 stocks a minute from Yahoo Finance, if the markets closed it will pull historical data every 10 minutes from alpha_vantage

I did all of this in Python 3.7
You will also need beautifulsoup4 and alpha_vantage from pip
You need to add a unique key for alpha vantage to work - https://www.alphavantage.co/support/#api-key
This is referenced under the variable key = ''


Should just run forever
