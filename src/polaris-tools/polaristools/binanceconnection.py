from datetime import datetime, timezone
import inspect
import os
import re
from time import time

import dateparser
import hashlib
import hmac
import pandas as pd
import pytz
import requests
from urllib.parse import urljoin, urlencode

from polaristools.utils import date_to_milliseconds
# importar logger

class BinanceConnection:
    baseurl_spot_margin = 'https://api.binance.com'
    baseurl_futures_usd = 'https://fapi.binance.com'
    baseurl_futures_coins = 'https://dapi.binance.com'

    def __init__(self):
        self.api_key = os.environ.get('binance_apikey'),
        self.api_secret = os.environ.get('binance_secretkey')
        self.headers = {'X-MBX-APIKEY': self.api_key[0]}

    def __requestUserdata(self, baseurl, endpoint, rmethod='get', **kwargs):
        payload = {}
        payload['recvWindow'] = 5000
        payload['timestamp'] = int(time()*1000)
        
        # Add other parameters before signature
        payload.update(kwargs)
        query_string = urlencode(payload)
        
        payload['signature'] = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        url = urljoin(baseurl,endpoint)
        
        request_params = dict(url=url, params=payload, headers=self.headers,)
        
        if rmethod=='get':
            response = requests.get(**request_params)
        elif rmethod=='post':
            response = requests.post(**request_params)
        elif rmethod=='delete':
            response = requests.delete(**request_params)
        
        if response.status_code != 200:
            print('Unsuccessful operation / code:400',inspect.currentframe().f_code.co_name)
            return response
        else:
            return response.json()

    def __request(self, baseurl, endpoint, rmethod='get', **kwargs):
        payload = {}
        
        if kwargs:
            payload.update(kwargs)
        url = (baseurl + endpoint)
        
        if rmethod == 'get':
            response = requests.get(url=url, params=payload)
        
        if response.status_code != 200:
            print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
            return response
        else:
            return response.json()


    #  *** FUTURES // MARKET DATA ENDPOINTS ***
    def futuresTestConnectivity(self, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/ping'):
        ''' 
            Test Connectivity
            GET /fapi/v1/ping
            Test connectivity to the Rest API.
            Weight: 1
            Parameters: NONE
            '''
        return self.__request(baseurl, endpoint)

    def futuresCheckserverTime(self, baseurl=baseurl_futures_usd,endpoint='/fapi/v1/time'):
        ''' 
            Check Server Time
            GET /fapi/v1/time
            Test connectivity to the Rest API and get the current server time.
            Weight: 1
            Parameters: NONE
            Response:{"serverTime": 1499827319559}
            '''
        return self.__request(baseurl, endpoint)

    def futuresExchangeInformation(self, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/exchangeInfo'):
        ''' 
            Exchange Information
            
            GET /fapi/v1/exchangeInfo
            
            Current exchange trading rules and symbol information
            Weight: 1
            Parameters: NONE
            '''
        return self.__request(baseurl, endpoint)

    def futuresOrderBook(self, symbol, limit=500, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/depth'):
        ''' 
            ORDER BOOK
            
            GET /fapi/v1/depth
            
            Weight:
            Adjusted based on the limit:
            Limit	          Weight
            5, 10, 20, 50	  2
            100	              5
            500	              10
            1000	          20
            
            Parameters:___________________________________________________________
            Name	Type	Mandatory	    Description
            symbol	STRING	YES	
            limit	INT	    NO	            Default 500;    Valid limits:[5, 10, 20, 50, 100, 500, 1000]
            
            Response:_______________________________________
            {
                "lastUpdateId": 1027024,
                "E": 1589436922972,   // Message output time
                "T": 1589436922959,   // Transaction time
                "bids": [
                    [
                      "4.00000000",     // PRICE
                      "431.00000000"    // QTY
                    ]
                ],
                "asks": [
                    [
                        "4.00000200",
                        "12.00000000"
                    ]
                ]   
            }
            '''
        return self.__request(
                            baseurl=baseurl,
                            endpoint=endpoint,
                            symbol=symbol,
                            limit=limit)

    def futuresMarkPrice(self, symbol, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/premiumIndex'):
        ''' 
            GET /fapi/v1/premiumIndex
            Mark Price and Funding Rate
            Weight: 1
            Parameters:
            Name	Type	Mandatory	Description
            symbol	STRING	NO          If no symbol are passed return a list of symbols 
            
            {
                "symbol": "BTCUSDT",
                "markPrice": "11793.63104562",  // mark price
                "indexPrice": "11781.80495970", // index price
                "estimatedSettlePrice": "11781.16138815", // Estimated Settle Price, only useful in the last hour before the settlement starts.
                "lastFundingRate": "0.00038246",  // This is the lasted funding rate
                "nextFundingTime": 1597392000000,
                "interestRate": "0.00010000",
                "time": 1597370495002
            }
            '''
        return self.__request(
                            baseurl=baseurl,
                            endpoint=endpoint,
                            symbol=symbol)

    def futuresGetFundingRateHistory(self, symbol, limit=100, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/fundingRate', **kwargs):
        ''' 
            Get Funding Rate History
            GET /fapi/v1/fundingRate

            Weight: 1
            Parameters:___________________________________________________________________________________
            Name	    Type	Mandatory	Description
            symbol	    STRING	NO	
            startTime	LONG	NO	Timestamp in ms to get funding rate from INCLUSIVE.
            endTime	    LONG	NO	Timestamp in ms to get funding rate until INCLUSIVE.
            limit	    INT	    NO	Default 100; max 1000
            If startTime and endTime are not sent, the most recent limit datas are returned.
            If the number of data between startTime and endTime is larger than limit, return as startTime + limit.
            In ascending order.
            '''
        payload = dict(
                    symbol=symbol,
                    limit=limit,
        )
        for k in kwargs:
            if k=='startTime':
                if isinstance(kwargs[k], str):
                    payload['startTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['startTime'] = kwargs[k]
            elif k=='endTime':
                if isinstance(kwargs[k], str):
                    payload['endTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['endTime'] = kwargs[k]
        return self.__request(baseurl,endpoint,**payload)

    def futuresTickerPriceChangeStatistics24h(self, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/ticker/24hr', **kwargs):
        ''' 
            24hr Ticker Price Change Statistics
            
            ET /fapi/v1/ticker/24hr
            
            24 hour rolling window price change statistics.
            Careful when accessing this with no symbol.
            
            Weight:_______________
            1   for a single symbol;
            40  when the symbol parameter is omitted
            Parameters:____________________________
            Name	Type	Mandatory	Description
            symbol	STRING	NO	
            * If the symbol is not sent, tickers for all symbols will be returned in an array.
            
            Response:
            {
                "symbol": "BTCUSDT",
                "priceChange": "-94.99999800",
                "priceChangePercent": "-95.960",
                "weightedAvgPrice": "0.29628482",
                "lastPrice": "4.00000200",
                "lastQty": "200.00000000",
                "openPrice": "99.00000000",
                "highPrice": "100.00000000",
                "lowPrice": "0.10000000",
                "volume": "8913.30000000",
                "quoteVolume": "15.30000000",
                "openTime": 1499783499040,
                "closeTime": 1499869899040,
                  "firstId": 28385,   // First tradeId
                  "lastId": 28460,    // Last tradeId
                  "count": 76         // Trade count
                }
            '''
        payload = {}
        if kwargs:
            payload['symbol'] = kwargs['symbol']
        return self.__request(baseurl, endpoint, **payload)

    def futuresSymbolPriceTicker(self, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/ticker/price', **kwargs):
        ''' 
            GET /fapi/v1/ticker/price

            Latest price for a symbol or symbols.
            
            Weight:
            1 for a single symbol;
            2 when the symbol parameter is omitted
            
            Parameters:______________________________________
            Name	Type	Mandatory	Description
            symbol	STRING	NO	
            If the symbol is not sent, prices for all symbols will be returned in an array.
            '''
        payload = {}
        if kwargs:
            payload['symbol'] = kwargs['symbol']
        return self.__request(baseurl, endpoint, **payload)

    def futuresOpenInterest(self, symbol, baseurl=baseurl_futures_usd, endpoint='/fapi/v1/openInterest'):
        ''' 
            Open Interest
            
            GET /fapi/v1/openInterest
            
            Get present open interest of a specific symbol.
            
            Weight: 1
            
            Parameters:
            
            Name	Type	Mandatory	Description
            symbol	STRING	YES
            
                Response:
            
            {
                "openInterest": "10659.509", 
                "symbol": "BTCUSDT",
                "time": 1589437530011   // Transaction time
            }
            '''
        return self.__request(
                            baseurl=baseurl,
                            endpoint=endpoint,
                            symbol=symbol)

    def futuresOpenInterestStatistics(self, symbol, period, limit=30, baseurl=baseurl_futures_usd, endpoint='/futures/data/openInterestHist', **kwargs):
        '''
            Open Interest Statistics
            
            GET /futures/data/openInterestHist

            Weight: 1
            Parameters:______________________________________________________
            Name	    Type	Mandatory	Description
            symbol	    STRING	YES	
            period	    ENUM	YES	        "5m","15m","30m","1h","2h","4h","6h","12h","1d"
            limit	    LONG	NO	        default 30, max 500
            startTime	LONG	NO	
            endTime	    LONG	NO	
            If startTime and endTime are not sent, the most recent data is returned.
            Only the data of the latest 30 days is available.
            '''
        payload = dict(
            symbol=symbol,
            period=period,
            limit=limit
        )
        for k in kwargs:
            if k=='startTime':
                if isinstance(kwargs[k], str):
                    payload['startTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['startTime'] = kwargs[k]
            elif k=='endTime':
                if isinstance(kwargs[k], str):
                    payload['endTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['endTime'] = kwargs[k]
        return self.__request(baseurl, endpoint, **payload)
    
    def futuresTopTraderLongShortRatio(self, ep_type, symbol, period, limit=30, baseurl=baseurl_futures_usd, **kwargs):
        ''' 
            Top Trader Long/Short Ratio (Accounts) or (Positions)
            
            GET /futures/data/topLongShortAccountRatio

            Weight: 1
            Parameters:__________________________________________________________
            Name	    Type	Mandatory	Description
            symbol	    STRING	YES	
            period	    ENUM	YES	        "5m","15m","30m","1h","2h","4h","6h","12h","1d"
            limit	    LONG	NO	        default 30, max 500
            startTime	LONG	NO	
            endTime	    LONG	NO	
            
            If startTime and endTime are not sent, the most recent data is returned.
            Only the data of the latest 30 days is available.
            '''
        if ep_type=='accounts':
            endpoint='/futures/data/topLongShortAccountRatio'
        elif ep_type=='positions':
            endpoint='/futures/data/topLongShortPositionRatio'
        payload = dict(
            symbol=symbol,
            period=period,
            limit=limit
        )
        for k in kwargs:
            if k=='startTime':
                if isinstance(kwargs[k], str):
                    payload['startTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['startTime'] = kwargs[k]
            elif k=='endTime':
                if isinstance(kwargs[k], str):
                    payload['endTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['endTime'] = kwargs[k]
        return self.__request(baseurl, endpoint, **payload)
    
    def futuresLongShortRatio(self, symbol, period, limit=30, baseurl=baseurl_futures_usd, endpoint='/futures/data/globalLongShortAccountRatio', **kwargs):
        ''' 
            Long/Short Ratio
            
            GET /futures/data/globalLongShortAccountRatio

            Weight: 1
            
            Parameters:
            
            Name	    Type	Mandatory	Description
            symbol	    STRING	YES	
            period	    ENUM	YES	        "5m","15m","30m","1h","2h","4h","6h","12h","1d"
            limit	    LONG	NO	         default 30, max 500
            startTime	LONG	NO	
            endTime	    LONG	NO	
            If startTime and endTime are not sent, the most recent data is returned.
            Only the data of the latest 30 days is available.
            '''
        payload = dict(
            symbol=symbol,
            period=period,
            limit=limit
        )
        for k in kwargs:
            if k=='startTime':
                if isinstance(kwargs[k], str):
                    payload['startTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['startTime'] = kwargs[k]
            elif k=='endTime':
                if isinstance(kwargs[k], str):
                    payload['endTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['endTime'] = kwargs[k]
        return self.__request(baseurl, endpoint, **payload)
    
    def futuresTakerBuySellVolume(self, symbol, period, limit=30, baseurl=baseurl_futures_usd, endpoint='/futures/data/takerlongshortRatio', **kwargs):
        ''' 
            Taker Buy/Sell Volume
            
            GET /futures/data/takerlongshortRatio

            Weight: 1
            Parameters:__________________________________________
            
            Name	    Type	Mandatory	Description
            symbol	    STRING	YES	
            period	    ENUM	YES	"5m","15m","30m","1h","2h","4h","6h","12h","1d"
            limit	    LONG	NO	default 30, max 500
            startTime	LONG	NO	
            endTime	    LONG	NO	
            
            If startTime and endTime are not sent, the most recent data is returned.
            Only the data of the latest 30 days is available.
            '''
        payload = dict(
            symbol=symbol,
            period=period,
            limit=limit
        )
        for k in kwargs:
            if k=='startTime':
                if isinstance(kwargs[k], str):
                    payload['startTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['startTime'] = kwargs[k]
            elif k=='endTime':
                if isinstance(kwargs[k], str):
                    payload['endTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['endTime'] = kwargs[k]
        return self.__request(baseurl, endpoint, **payload)


    # *** FUTURES // ACCOUNT-TRADES ENDPOINTS
    def futuresNewFutureAccountTransfer(self, asset, amount, type, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/futures/transfer'):
        ''' 
            New Future Account Transfer (USER_DATA)
            
            POST /sapi/v1/futures/transfer (HMAC SHA256)

            Execute transfer between spot account and futures account.
            
            Weight(IP): 1
            Parameters:__________________________________________________
            Name	    Type	Mandatory	Description
            asset	    STRING	YES	        The asset being transferred, e.g., USDT
            amount	    DECIMAL	YES	        The amount to be transferred
            type	    INT	    YES	        1: transfer from spot account to USDT-Ⓜ futures account.
                                            2: transfer from USDT-Ⓜ futures account to spot account.
                                            3: transfer from spot account to COIN-Ⓜ futures account.
                                            4: transfer from COIN-Ⓜ futures account to spot account.
            recvWindow	LONG	NO	
            timestamp	LONG	YES
            '''
        payload = dict(
            asset=asset,
            amount=amount,
            type=type,
        )
        url = urljoin(baseurl, endpoint)
        response = requests.post(url, params=payload,)
        if response.status_code != 200:
            print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
            return response
        else:
            return response.json()


    # *** SPOT MARGIN // WALLET ENDPOINTS***
    # System, get
    def systemStatus(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/system/status'):
        ''' 
        System Status (System)
        GET /sapi/v1/system/status
        '''
        url       =  baseurl + endpoint
        response  = requests.get(url=url)
        if response.status_code != 200:
            print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
            return response.status_code
        else:
            msg = response.json()['msg']
            status = response.json()['status']
            return f'System Status : {msg}'

    # Userdata, get
    def allCoinsInfo(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/capital/config/getall'): 
        ''' 
            All Coins' Information (USER_DATA)
            Get information of coins (available for deposit and withdraw) for user.
            GET /sapi/v1/capital/config/getall (HMAC SHA256)
        
            '''
        return self.__requestUserdata(baseurl,endpoint)

    # Userdata, get
    def dailyAccountSnapshot(self, type, limit=15, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/accountSnapshot'):
        ''' 
            Daily Account Snapshot (USER_DATA)
            GET /sapi/v1/accountSnapshot (HMAC SHA256)
            Parameters:
            Name            Type	Mandatory  Description
            type            STRING	YES        "SPOT", "MARGIN", "FUTURES"
            startTime       LONG	NO	
            endTime         LONG	NO	
            limit           INT	    NO	       min 7, max 30, default 7
            recvWindow      LONG	NO	
            timestamp       LONG	YES	
            
            The query time period must be less then 30 days
            Support query within the last one month only
            If startTimeand endTime not sent, return records of the last 7 days by default
            
            expected return - > dict_keys(['code', 'msg', 'snapshotVos'])
            '''
        response = self.__requestUserdata(
                                        baseurl  = baseurl,
                                        endpoint = endpoint,
                                        type     = type,
                                        limit    = limit,
        )
        snapshotVos = response['snapshotVos']
        # btc_quoted = totalAssetOfBtc * self.currentAveragePrice('btcusdt')
        return snapshotVos

    # Userdata, get
    def accountStatus(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/account/status'):
        ''' 
            Account Status (USER_DATA) 
            GET /sapi/v1/account/status
            
            Fetch account status detail.
            Weight(IP): 1
            Parameters:
            
            Name        Type	Mandatory	Description
            recvWindow	LONG	NO	
            timestamp	LONG	YES
            '''
        return self.__requestUserdata(baseurl,endpoint)

    # Userdata, get
    def accountApiTradingStatus(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/account/apiTradingStatus'):
        '''
            Account API Trading Status (USER_DATA) 
            GET /sapi/v1/account/apiTradingStatus (HMAC SHA256)
            Fetch account api trading status detail.
            Weight(IP): 1
            Parameters:
            Name        Type	Mandatory	Description
            recvWindow	LONG	NO	
            timestamp	LONG	YES
            '''
        return self.__requestUserdata(baseurl,endpoint)

    # Userdata, get
    def dustLog (self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/asset/dribblet'):
        ''' 
            DustLog(USER_DATA) 
            GET /sapi/v1/asset/dribblet (HMAC SHA256)
            Parameters:
            Name       Type	Mandatory	Description
            startTime  LONG	NO	
            endTime    LONG	NO	
            recvWindow LONG	NO	
            timestamp  LONG	YES	
            Only return last 100 records
            Only return records after 2020/12/01
            '''
        resp = self.__requestUserdata(baseurl, endpoint)
        try:
            total = resp['total']
            df = pd.DataFrame.from_dict(resp['userAssetDribblets'][0])
            df['operateTime'] = pd.to_datetime(df['operateTime'],   unit='ms')
            df_2 = pd.DataFrame(resp['userAssetDribblets'][0]['userAssetDribbletDetails'])
            df_2['operateTime'] = pd.to_datetime(df_2['operateTime'],   unit='ms')
            
            print(f"""Dustlog, Total : {total}""")
            print(' Operations\n',30*'#')
            print(df,'\n')
            # userAssetDribbletDetails
            print(' User Asset Dribblet Details\n',30*'#')
            print(df_2)
        except:
            print('Error obteniendo la información. ',__name__)

    # Userdata, post
    def getAssetsThatCanBeConvertedIntoBNB(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/asset/dust-btc'):
        ''' 
            Get Assets That Can Be Converted Into BNB (USER_DATA) 
            POST /sapi/v1/asset/dust-btc (HMAC SHA256)
            Weight(IP): 1
            Parameters:
            
            Name	Type	Mandatory	Description
            recvWindow	LONG	NO	
            timestamp	LONG	YES
            '''
        return self.__requestUserdata(baseurl, endpoint, rmethod='post')

    # Userdata, post. ***NO PROBADO
    def dustTransfer(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/asset/dust'):
        ''' 
            Dust Transfer (USER_DATA) 
            POST /sapi/v1/asset/dust (HMAC SHA256)
            Convert dust assets to BNB.
            
            Weight(UID): 10
            Parameters:
            Name        Type	Mandatory	 Description
            asset   	ARRAY	YES	         The asset being converted. For example: asset=BTC&asset=USDT
            recvWindow	LONG	NO	
            timestamp	LONG	YES	
            
            You need to openEnable Spot & Margin Trading permission for the API Key which requests this endpoint.
            '''
        return self.__requestUserdata(baseurl, endpoint, rmethod='post', asset=['BTC','USDT'])
    
    # Userdata, get
    def assetDividendRecord(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/asset/assetDividend'):
        '''
            Asset Dividend Record (USER_DATA) 
            GET /sapi/v1/asset/assetDividend (HMAC SHA256)
            Query asset dividend record.
            Weight(IP): 10
            Parameters:
            Name	    Type	Mandatory	Description
            asset	    STRING	NO	
            startTime	LONG	NO	
            endTime	    LONG	NO	
            limit	    INT	    NO	       Default 20, max 500
            recvWindow	LONG	NO	
            timestamp	LONG	YES
            '''
        return self.__requestUserdata(baseurl=baseurl, endpoint=endpoint, limit=500)

    # Userdata, get
    def assetDetail(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/asset/assetDetail'):
        '''
            Asset Detail (USER_DATA)     
            GET /sapi/v1/asset/assetDetail (HMAC SHA256)
            Fetch details of assets supported on Binance.
            Weight(IP): 1
            Parameters:
            Name        Type	Mandatory	Description
            asset       STRING	NO	
            recvWindow	LONG	NO	
            timestamp	LONG	YES	
            ***Please get network and other deposit or withdraw details from GET /sapi/v1/capital/config/getall.
            '''
        return self.__requestUserdata(baseurl, endpoint)

    # Userdata, get
    def tradeFee(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/asset/tradeFee'):
        ''' 
            Trade Fee (USER_DATA)
            GET /sapi/v1/asset/tradeFee (HMAC SHA256)
            Fetch trade fee
            Weight(IP): 1
            Parameters:
            Name	    Type	Mandatory	Description
            symbol	    STRING	NO	
            recvWindow	LONG	NO	
            timestamp	LONG	YES
            '''
        return self.__requestUserdata(baseurl, endpoint)

    # Userdata, post. ***NO PROBADO
    def userUniversalTransfer(self, endpoint='/sapi/v1/asset/transfer'):
        ''' 
            User Universal Transfer (USER_DATA)
            POST /sapi/v1/asset/transfer (HMAC SHA256)
        
            You need to enable Permits Universal Transfer option for the API Key which requests this endpoint.
            Response : {"tranId":13526853623}
            
            Weight(IP): 1
            Parameters:
            Name	    Type	Mandatory	Description
            type	    ENUM	YES	
            asset	    STRING	YES	
            amount	    DECIMAL	YES	
            fromSymbol	STRING	NO	
            toSymbol	STRING	NO	
            recvWindow	LONG	NO	
            timestamp	LONG	YES	
            
            fromSymbol  must be sent when type are ISOLATEDMARGIN_MARGIN and ISOLATEDMARGIN_ISOLATEDMARGIN
            toSymbol    must be sent when type are MARGIN_ISOLATEDMARGIN and ISOLATEDMARGIN_ISOLATEDMARGIN
            
            ENUM of transfer types:
                MAIN_UMFUTURE                 Spot account transfer to USDⓈ-M Futures account
                MAIN_CMFUTURE                 Spot account transfer to COIN-M Futures account
                MAIN_MARGIN                   Spot account transfer to Margin（cross）account
                UMFUTURE_MAIN                 USDⓈ-M Futures account transfer to Spot account
                UMFUTURE_MARGIN               USDⓈ-M Futures account transfer to Margin（cross）account
                CMFUTURE_MAIN                 COIN-M Futures account transfer to Spot account
                CMFUTURE_MARGIN               COIN-M Futures account transfer to Margin(cross) account
                MARGIN_MAIN                   Margin（cross）account transfer to Spot account
                MARGIN_UMFUTURE               Margin（cross）account transfer to USDⓈ-M Futures
                MARGIN_CMFUTURE               Margin（cross）account transfer to COIN-M Futures
                ISOLATEDMARGIN_MARGIN         Isolated margin account transfer to Margin(cross) account
                MARGIN_ISOLATEDMARGIN         Margin(cross) account transfer to Isolated margin account
                ISOLATEDMARGIN_ISOLATEDMARGIN Isolated margin account transfer to Isolated margin account
                MAIN_FUNDING                  Spot account transfer to Funding account
                FUNDING_MAIN                  Funding account transfer to Spot account
                FUNDING_UMFUTURE              Funding account transfer to UMFUTURE account
                UMFUTURE_FUNDING              UMFUTURE account transfer to Funding account
                MARGIN_FUNDING                MARGIN account transfer to Funding account
                FUNDING_MARGIN                Funding account transfer to Margin account
                FUNDING_CMFUTURE              Funding account transfer to CMFUTURE account
                CMFUTURE_FUNDING              CMFUTURE account transfer to Funding account
            '''
        return self.__requestUserdata(
                                        type, 
                                        asset,
                                        endpoint=endpoint, 
                                        rmethod='post'
                                        )

    # Userdata, get. ***NO PROBADO
    def queryUserUniversalTransferHistory(self, endpoint='/sapi/v1/asset/transfer'):
        ''' 
            Query User Universal Transfer History (USER_DATA) 
            GET /sapi/v1/asset/transfer (HMAC SHA256)
            
            Weight(IP): 1
            
            Parameters:
            
            Name	    Type	Mandatory	Description
            type	    ENUM	YES	
            startTime	LONG	NO	
            endTime	    LONG	NO	
            current	    INT	    NO	        Default 1
            size	    INT	    NO	        Default 10, Max 100
            fromSymbol	STRING	NO	
            toSymbol	STRING	NO	
            recvWindow	LONG	NO	
            timestamp	LONG	YES	
            
            fromSymbol must be sent when type are ISOLATEDMARGIN_MARGIN and ISOLATEDMARGIN_ISOLATEDMARGIN
            toSymbol must be sent when type are MARGIN_ISOLATEDMARGIN and ISOLATEDMARGIN_ISOLATEDMARGIN
            Support query within the last 6 months only
            If startTimeand endTime not sent, return records of the last 7 days by default
            '''
        pass

    # Userdata, post.
    def fundingWallet(self, endpoint='/sapi/v1/asset/get-funding-asset'):
        ''' 
            Funding Wallet (USER_DATA)
            POST /sapi/v1/asset/get-funding-asset (HMAC SHA256)
            Weight(IP): 1
            
            Parameters:
            Name	            Type	Mandatory	Description
            asset	            STRING	NO	
            needBtcValuation	STRING	NO	        true or false
            recvWindow	        LONG	NO	
            timestamp	        LONG	YES	
            
            Currently supports querying the following business assets：Binance Pay, Binance Card, Binance Gift Card, Stock Token
            '''
        return self.__requestUserdata(
                                    endpoint=endpoint, 
                                    rmethod='post'
                                    )

    # Userdata, get.
    def getApiKeyPermission(self, baseurl=baseurl_spot_margin, endpoint='/sapi/v1/account/apiRestrictions'):
        ''' 
            Get API Key Permission (USER_DATA) 
            GET /sapi/v1/account/apiRestrictions (HMAC SHA256)
            Weight(IP): 1
            Parameters:
            Name	    Type	Mandatory	Description
            recvWindow	LONG	NO	
            timestamp	LONG	YES
            '''
        return self.__requestUserdata(baseurl, endpoint)


    # *** SPOT MARGIN // MARKET DATA ENDPOINTS
    # get
    def testConnectivity(self, baseurl=baseurl_spot_margin, endpoint='/api/v3/ping'):
        '''
            GET /api/v3/ping 
            '''
        r = requests.get(baseurl, endpoint)
        return r.json()

    # get
    def checkServerTime(self):
        ''' 
            GET /api/v3/time 
            '''
        endpoint = '/api/v3/time'
        r = requests.get(url=self.baseurl_spot_margin+endpoint)
        if r.status_code != 200:
            print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
        else:
            return r.json()

    # get
    def currentAveragePrice(self,symbol):
        '''
            Current Average Price
            GET /api/v3/avgPrice
            Parameters:
            Name	Type	Mandatory	Description
            symbol	STRING	YES	
            Data Source: Memory
            *Current average price for a symbol.
            '''
        endpoint    = '/api/v3/avgPrice'
        payload     = {'symbol': symbol.upper()}
        url = urljoin(self.baseurl_spot_margin, endpoint)
        response = requests.get(url=url,params=payload)
        if response.status_code != 200:
            print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
            return response.status_code
        else:
            r = response.json()
            return float(r['price'])

    # get
    def tickerPriceChangeStatistics24hRoll(self, **kwargs):
        ''' 24hr Ticker Price Change Statistics
            GET /api/v3/ticker/24hr
            24 hour rolling window price change statistics. 
            Careful when accessing this with no symbol.
            
            Weight(IP):_______________________________________
            Parameter   Symbols Provided                Weight
            symbol	    1                               1
                        symbol parameter is omitted	    40
            symbols     1-20	                        1
                        21-100	                        20
                        101 or more	                    40
                        symbols parameter is omitted	40
            
            Parameters:___________________________________
            Name	Type	Mandatory     Description
            symbol	STRING	NO	          Parameter symbol and symbols cannot be used in combination.
                                            If neither parameter is sent, tickers for all symbols will be returned in an array.
            symbols	STRING	NO            Examples of accepted format for the symbols parameter: ["BTCUSDT","BNBUSDT"]
                                            or
                                            %5B%22BTCUSDT%22,%22BNBUSDT%22%5D
            
            Data Source: Memory
            '''
        endpoint = '/api/v3/ticker/24hr'
        payload = {}
        if kwargs:
            payload.update(kwargs)
        url = urljoin(self.baseurl_spot_margin, endpoint)
        response = requests.get(
                                url=url,
                                params=payload
                                )
        if response.status_code != 200:
            print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
            return response
        else:
            return response.json()

    # get
    def klineCandlestick(self, symbol, interval, endpoint='/api/v3/klines', **kwargs):
        ''' 
            Kline/Candlestick Data
            GET /api/v3/klines

            Kline/candlestick bars for a symbol.
            Klines are uniquely identified by their open time.
            Weight(IP): 1
            Parameters:
            
            Name        Type	Mandatory      Description
            symbol      STRING	YES            e.g 'BTCUSDT'
            interval	ENUM	YES            e.g'1m, 1h,1d, etc'	
            startTime	LONG	NO	
            endTime	    LONG	NO	
            limit       INT     NO          Default 500; max 1000.
            
            If startTime and endTime are not sent, the most recent klines are returned.
            Data Source: Database
            '''
        payload = dict(symbol=symbol, interval=interval)
        for k in kwargs:
            if k=='startTime':
                if isinstance(kwargs[k], str):
                    payload['startTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['startTime'] = kwargs[k]
            elif k=='endTime':
                if isinstance(kwargs[k], str):
                    payload['endTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['endTime'] = kwargs[k]
            elif k=='limit':
                payload['limit'] = kwargs[k]
        url = urljoin(self.baseurl_spot_margin, endpoint)
        r = requests.get(url, params=payload,)
        if r.status_code != 200:
            print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
            return r.status_code
        else:
            return r.json()

    # get
    def futuresContinuousKlines(self,pair,interval,endpoint='/fapi/v1/continuousKlines',**kwargs):
        ''' 
            Continuous Contract Kline/Candlestick Data 
            GET /fapi/v1/continuousKlines
            
            Kline/candlestick bars for a specific contract type.
            Klines are uniquely identified by their open time.
            Weight: based on parameter LIMIT
            
            LIMIT	    weight
            [1,100)	    1
            [100, 500)	2
            [500, 1000]	5
            > 1000	    10
            
            Parameters:
            Name	       Type	    Mandatory	Description
            pair	       STRING	YES	
            contractType   ENUM	    YES	
            interval	   ENUM	    YES	
            startTime	   LONG	    NO	
            endTime	       LONG	    NO	
            limit	       INT	    NO	        Default 500; max 1500.
            
            If startTime and endTime are not sent, the most recent klines are returned.
            
            Contract type:
                PERPETUAL
                CURRENT_QUARTER
                NEXT_QUARTER
            '''
        baseurl = self.baseurl_futures_usd
        payload = dict(
            pair = pair,
            interval = interval,
            contractType = 'PERPETUAL'
        )
        for k in kwargs:
            if k=='startTime':
                if isinstance(kwargs[k], str):
                    payload['startTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['startTime'] = kwargs[k]
            elif k=='endTime':
                if isinstance(kwargs[k], str):
                    payload['endTime'] = date_to_milliseconds(kwargs[k])
                elif isinstance(kwargs[k], int):
                    payload['endTime'] = kwargs[k]
            elif k=='limit':
                payload['limit'] = kwargs[k]
        url = urljoin(baseurl, endpoint)
        r = requests.get(url, params=payload,)
        
        if r.status_code != 200:
            # print('Unsuccessful operation', inspect.currentframe().f_code.co_name)
            return r
        else:
            return r.json()

    def getEarliestValidTimestamp(self, symbol, interval, stream_type):
        """
            Get earliest valid open timestamp from Binance
            :param symbol: Name of symbol pair e.g BNBBTC
            :type symbol: str
            :param interval: Binance Kline interval
            :type interval: str
            :param klines_type: Historical klines type: SPOT or FUTURES
            :type klines_type: HistoricalKlinesType
            :return: first valid timestamp
            """
        if stream_type=='klines':
            data = self.klineCandlestick(
                symbol=symbol, 
                interval=interval,
                startTime=0,
                endTime=time()*1000,
                limit=1
            )
        elif stream_type=='continuous_klines':
            data = self.futuresContinuousKlines(
                pair=symbol, 
                interval=interval,
                startTime=0,
                endTime=time()*1000,
                limit=1
            )
        else:
            return f"INVALID PARAMETERS ENTERED {__name__}"
        return data[0][0]
            

    # *** SPOT MARGIN // ACCOUNT ENDPOINTS
    # Trade, post
    def testNewOrder(self,symbol,side,type,timeInForce,quantity,price,endpoint='/api/v3/order/test',**kwargs):
        ''' 
            Test New Order (TRADE)
            POST /api/v3/order/test (HMAC SHA256)
            Test new order creation and signature/recvWindow long. 
            Creates and validates a new order but does not send it into the matching engine.
            
            Parameters:

            Name	          Type	   Mandatory	Description
            symbol	          STRING   YES	
            side	          ENUM	   YES	
            type	          ENUM	   YES	
            timeInForce	      ENUM	   YES	
            quantity	      DECIMAL  YES	
            quoteOrderQty	  DECIMAL  NO	
            price	          DECIMAL  YES	
            newClientOrderId  STRING   NO	        A unique id among open orders. Automatically generated if not sent.
            stopPrice	      DECIMAL  NO	        Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders.
            trailingDelta	  LONG	   NO	        Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders. For more details on SPOT implementation on trailing stops, please refer to Trailing Stop FAQ
            icebergQty	      DECIMAL  NO	        Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT to create an iceberg order.
            newOrderRespType  ENUM	   NO	        Set the response JSON. ACK, RESULT, or FULL; MARKET and LIMIT order types default to FULL, all other orders default to ACK.
            recvWindow	      LONG	   NO	        The value cannot be greater than 60000
            timestamp	      LONG	   YES	
            
            Additional mandatory parameters based on type:
            _____________________________________________
            Type	Additional mandatory parameters
            LIMIT	timeInForce, quantity, price
            MARKET	quantity or quoteOrderQty
            STOP_LOSS	quantity, stopPrice or trailingDelta
            STOP_LOSS_LIMIT	timeInForce, quantity, price, stopPrice or trailingDelta
            TAKE_PROFIT	quantity, stopPrice or trailingDelta
            TAKE_PROFIT_LIMIT	timeInForce, quantity, price, stopPrice or trailingDelta
            LIMIT_MAKER	quantity, price
            Other info:
            
            LIMIT_MAKER are LIMIT orders that will be rejected if they would immediately match and trade as a taker.
            STOP_LOSS and TAKE_PROFIT will execute a MARKET order when the stopPrice is reached.
            Any LIMIT or LIMIT_MAKER type order can be made an iceberg order by sending an icebergQty.
            Any order with an icebergQty MUST have timeInForce set to GTC.
            MARKET orders using the quantity field specifies the amount of the base asset the user wants to buy or sell at the market price.
            For example, sending a MARKET order on BTCUSDT will specify how much BTC the user is buying or selling.
            MARKET orders using quoteOrderQty specifies the amount the user wants to spend (when buying) or receive (when selling) the quote asset; the correct quantity will be determined based on the market liquidity and quoteOrderQty.
            Using BTCUSDT as an example:
            On the BUY side, the order will buy as many BTC as quoteOrderQty USDT can.
            On the SELL side, the order will sell as much BTC needed to receive quoteOrderQty USDT.
            MARKET orders using quoteOrderQty will not break LOT_SIZE filter rules; the order will execute a quantity that will have the notional value as close as possible to quoteOrderQty.
            same newClientOrderId can be accepted only when the previous one is filled, otherwise the order will be rejected.
            For STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT_LIMIT and TAKE_PROFIT orders, trailingDelta can be combined with stopPrice.
            Trigger order price rules against market price for both MARKET and LIMIT versions:
            
            Price above market price: STOP_LOSS BUY, TAKE_PROFIT SELL
            Price below market price: STOP_LOSS SELL, TAKE_PROFIT BUY
            Data Source: Matching Engine
            
            Response:{}
            '''
        mandatory = dict( 
                        symbol=symbol,
                        side=side,
                        type=type,
                        timeInForce=timeInForce,
                        quantity=quantity,
                        price=price,
                        )
        mandatory.update(kwargs)
        return self.__requestUserdata(
                                    endpoint=endpoint,
                                    rmethod='post',
                                    **mandatory
                                    )

    # Trade, post. No probado
    def newOrder(self, symbol, side, type, endpoint='/api/v3/order', **kwargs):
        '''
            New Order (TRADE) 
            POST /api/v3/order (HMAC SHA256)
                Send in a new order.
                Weight(UID): 1 Weight(IP): 1
                Parameters:
                Name	            Type	Mandatory	Description
                symbol	            STRING	YES	
                side	            ENUM	YES	
                type	            ENUM	YES	
                timeInForce	        ENUM	NO	
                quantity	        DECIMAL	NO	
                quoteOrderQty       DECIMAL	NO	
                price	            DECIMAL	NO	
                newClientOrderId	STRING	NO	A unique id among open orders. Automatically generated if not sent.
                stopPrice	        DECIMAL	NO	Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders.
                trailingDelta	    LONG	NO	Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders. For more details on SPOT implementation on trailing stops, please refer to Trailing Stop FAQ
                icebergQty	        DECIMAL	NO	Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT to create an iceberg order.
                newOrderRespType	ENUM	NO	Set the response JSON. ACK, RESULT, or FULL; MARKET and LIMIT order types default to FULL, all other orders default to ACK.
                recvWindow	        LONG	NO	The value cannot be greater than 60000
                timestamp	        LONG	YES	
                
                Additional mandatory parameters based on type:
                
                Type	           Additional mandatory parameters
                LIMIT	           timeInForce, quantity, price
                MARKET	           quantity or quoteOrderQty
                STOP_LOSS	       quantity, stopPrice or trailingDelta
                STOP_LOSS_LIMIT	   timeInForce, quantity, price, stopPrice or trailingDelta
                TAKE_PROFIT	       quantity, stopPrice or trailingDelta
                TAKE_PROFIT_LIMIT  timeInForce, quantity, price, stopPrice or trailingDelta
                LIMIT_MAKER	       quantity, price
                Other info:
                
                LIMIT_MAKER are LIMIT orders that will be rejected if they would immediately match and trade as a taker.
                STOP_LOSS and TAKE_PROFIT will execute a MARKET order when the stopPrice is reached.
                Any LIMIT or LIMIT_MAKER type order can be made an iceberg order by sending an icebergQty.
                Any order with an icebergQty MUST have timeInForce set to GTC.
                MARKET orders using the quantity field specifies the amount of the base asset the user wants to buy or sell at the market price.
                For example, sending a MARKET order on BTCUSDT will specify how much BTC the user is buying or selling.
                MARKET orders using quoteOrderQty specifies the amount the user wants to spend (when buying) or receive (when selling) the quote asset; the correct quantity will be determined based on the market liquidity and quoteOrderQty.
                
                Using BTCUSDT as an example:
                On the BUY side, the order will buy as many BTC as quoteOrderQty USDT can.
                On the SELL side, the order will sell as much BTC needed to receive quoteOrderQty USDT.
                MARKET orders using quoteOrderQty will not break LOT_SIZE filter rules; the order will execute a quantity that will have the notional value as close as possible to quoteOrderQty.
                same newClientOrderId can be accepted only when the previous one is filled, otherwise the order will be rejected.
                For STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT_LIMIT and TAKE_PROFIT orders, trailingDelta can be combined with stopPrice.
                Trigger order price rules against market price for both MARKET and LIMIT versions:
                
                Price above market price: STOP_LOSS BUY, TAKE_PROFIT SELL
                Price below market price: STOP_LOSS SELL, TAKE_PROFIT BUY
                Data Source: Matching Engine
                '''
        mandatory = dict( 
                        symbol=symbol,
                        side=side,
                        type=type,
                        )
        mandatory.update(kwargs)
        return self.__requestUserdata(
                                    endpoint=endpoint,
                                    rmethod='post',
                                    **mandatory
                                    )

    # Trade, delete. No probado
    def cancelOrder(self, symbol, orderId, endpoint='/api/v3/order', **kwargs):
        '''
            Cancel Order (TRADE) 
            DELETE /api/v3/order (HMAC SHA256)
            Cancel an active order.
            Weight(IP): 1
            Parameters:
            
            Name	            Type	Mandatory	Description
            symbol	            STRING	YES	
            orderId	            LONG	NO	
            origClientOrderId	STRING	NO	
            newClientOrderId	STRING	NO	Used to uniquely identify this cancel. Automatically generated by default.
            recvWindow	        LONG	NO	The value cannot be greater than 60000
            timestamp	        LONG	YES	
            
            Either orderId or origClientOrderId must be sent. 
            If both orderId and origClientOrderId are provided, 
            orderId takes precedence.
            Data Source: Matching Engine
            '''
        mandatory = dict(
                        symbol=symbol,
                        orderId=orderId,
                        )
        mandatory.update(kwargs)
        return self.__requestUserdata(
                                    endpoint=endpoint,
                                    rmethod='delete',
                                    **mandatory
                                    )

    # Trade, delete. No probado
    def cancelAllOpenOrdersOnASymbol(self, symbol, endpoint='/api/v3/openOrders'):
        '''
            Cancel all Open Orders on a Symbol (TRADE) 
            DELETE /api/v3/openOrders
            Cancels all active orders on a symbol.
            This includes OCO orders.
            
            Weight(IP): 1
            
            Parameters
            
            Name	    Type	Mandatory	Description
            symbol	    STRING	YES	
            recvWindow	LONG	NO	        The value cannot be greater than 60000
            timestamp	LONG	YES	
            
            Data Source: Matching Engine
            '''
        return self.__requestUserdata(
                                    endpoint=endpoint,
                                    rmethod='delete',
                                    symbol=symbol
                                    )

    # Userdata, get. No probado
    def queryOrder(self,symbol, endpoint='/api/v3/order', **kwargs):
        '''
            Query Order (USER_DATA) 
            GET /api/v3/order (HMAC SHA256)
            Check an order's status.
            Weight(IP): 2
            Parameters:
            
            Name	            Type	Mandatory	Description
            symbol	            STRING	YES	
            orderId	            LONG	NO          *	
            origClientOrderId	STRING	NO	        *
            recvWindow	        LONG	NO	        The value cannot be greater than 60000
            timestamp	        LONG	YES	
            
            Notes:
            Either orderId or origClientOrderId must be sent.
            For some historical orders cummulativeQuoteQty will be < 0, meaning the data is not available at this time.
            Data Source: Database
            '''
        # orderId = int()
        # origClientOrderId = str()
        mandatory = dict(symbol=symbol)
        mandatory.update(kwargs)
        return self.__requestUserdata(
                                    endpoint=endpoint,
                                    rmethod='get',
                                    **mandatory
                                    )

    # Userdata, get.
    def currentOpenOrders(self, baseurl=baseurl_spot_margin,endpoint='/api/v3/openOrders'):
        ''' 
            Current Open Orders (USER_DATA)
            GET /api/v3/openOrders (HMAC SHA256)
            Get all open orders on a symbol. Careful when accessing this with no symbol.
            Weight(IP): 3 for a single symbol; 40 when the symbol parameter is omitted;
            Parameters:
            Name	    Type	Mandatory	Description
            symbol	    STRING	NO	
            recvWindow	LONG	NO	        The value cannot be greater than 60000
            timestamp	LONG	YES	
            
            If the symbol is not sent, orders for all symbols will be returned in an array.
            Data Source: Database
            '''
        return self.__requestUserdata(
            baseurl=baseurl,
            endpoint=endpoint,
        )

    # Userdata, get. No probado
    def allOrders(self, symbol,endpoint='/api/v3/allOrders'):
        '''
            All Orders (USER_DATA) 
            GET /api/v3/allOrders (HMAC SHA256)
            Get all account orders; active, canceled, or filled.
            Weight(IP): 10 with symbol
            Parameters:
            
            Name	    Type	Mandatory	Description
            symbol	    STRING	YES	
            orderId	    LONG	NO	
            startTime	LONG	NO	
            endTime	    LONG	NO	
            limit	    INT	    NO	        Default 500; max 1000.
            recvWindow	LONG	NO	        The value cannot be greater than 60000
            timestamp	LONG	YES	
            
            Notes:________________________________________________________
            If orderId is set, it will get orders >= that orderId. Otherwise most recent orders are returned.
            For some historical orders cummulativeQuoteQty will be < 0, meaning the data is not available at this time.
            If startTime and/or endTime provided, orderId is not required.
            Data Source: Database
            '''
        return self.__requestUserdata(
                                    endpoint,
                                    rmethod='get',
                                    symbol=symbol
                                    )


    ''' OCO ORDERS WILL BE HERE '''

    # Userdata, get. No probado
    def accountInformation(self, endpoint='/api/v3/account'):
        '''
            Account Information (USER_DATA) 
            GET /api/v3/account (HMAC SHA256)
            Get current account information.
            Weight(IP): 10
            Parameters:
            
            Name	    Type	Mandatory	Description
            recvWindow	LONG	NO	        The value cannot be greater than 60000
            timestamp	LONG	YES	
            
            Data Source: Memory => Database
            '''
        return self.__requestUserdata(
            baseurl=self.baseurl_spot_margin,
            endpoint=endpoint
        )

    # Userdata, get. No probado
    def accountTradeList(self, symbol, endpoint='/api/v3/myTrades', **kwargs):
        '''
            Account Trade List (USER_DATA)
            GET /api/v3/myTrades (HMAC SHA256)
            Get trades for a specific account and symbol.
            Weight(IP): 10
            Parameters:
            
            Name	    Type	Mandatory	Description
            symbol	    STRING	YES	
            orderId	    LONG	NO	        This can only be used in combination with symbol.
            startTime	LONG	NO	
            endTime	    LONG	NO	
            fromId	    LONG	NO	        TradeId to fetch from. Default gets most recent trades.
            limit	    INT	    NO	        Default 500; max 1000.
            recvWindow	LONG	NO	        The value cannot be greater than 60000
            timestamp	LONG	YES	
            
            Notes:
            If fromId is set, it will get id >= that fromId. Otherwise most recent trades are returned.
            Data Source: Database
            '''
        mandatory = dict(symbol=symbol)
        mandatory.update(kwargs)
        return self.__requestUserdata(
                                    endpoint,
                                    **mandatory
                                    )

    # Trade, get. No probado
    def queryCurrentOrderCountUsage(self, endpoint='/api/v3/rateLimit/order'):
        '''
            Query Current Order Count Usage (TRADE)
            GET /api/v3/rateLimit/order
            Displays the user's current order count usage for all intervals.
            Weight(IP): 20
            Parameters:
            
            Name	    Type	Mandatory	Description
            recvWindow	LONG	NO	        The value cannot be greater than 60000
            timestamp	LONG	YES	
            
            Data Source: Memory
            '''
        return self.__requestUserdata(endpoint)


if __name__== '__main__':

    from polaristools.polarisbot import BinanceConnection
    binance = BinanceConnection()

    
    binance.futuresTestConnectivity()
    binance.futuresCheckserverTime()
    
    var = binance.futuresExchangeInformation()
    type(var)
    len(var)
    
    var = binance.futuresOrderBook(symbol='BNBUSDT')
    type(var)
    len(var)
    
    var = binance.futuresMarkPrice(symbol='ADAUSDT')
    type(var)
    len(var)
    
    var = binance.futuresGetFundingRateHistory(symbol='ADAUSDT')
    type(var)
    len(var)
    
    var = binance.futuresTickerPriceChangeStatistics24h()
    type(var)
    len(var)
    
    var = binance.futuresSymbolPriceTicker()
    type(var)
    len(var)
    
    var = binance.futuresOpenInterest(symbol='ADAUSDT')
    type(var)
    len(var)
    
    var = binance.futuresOpenInterestStatistics(symbol='ADAUSDT', period='5m')
    type(var)
    len(var)
    
    var = binance.futuresTopTraderLongShortRatio(ep_type='positions', symbol='ADAUSDT', period='5m')
    type(var)
    len(var)
    
    var = binance.futuresLongShortRatio(symbol='ADAUSDT', period='5m')
    type(var)
    len(var)
    
    var = binance.futuresTakerBuySellVolume(symbol='ADAUSDT', period='5m')
    type(var)
    len(var)
    
    # *** PENDING ***
    binance.futuresNewFutureAccountTransfer(asset, amount, type)
    
    var = binance.systemStatus()
    type(var)
    len(var)
    
    var = binance.allCoinsInfo()
    type(var)
    len(var)
    
    var = binance.dailyAccountSnapshot(type='SPOT')
    len(var)
    var[0].keys()
    var = binance.dailyAccountSnapshot(type='FUTURES')
    type(var)
    len(var)
    
    var = binance.accountStatus()
    type(var)
    len(var)
    
    var = binance.accountApiTradingStatus()
    type(var)
    len(var)
    var
    
    var = binance.dustLog()
    type(var)
    len(var)
    
    var = binance.getAssetsThatCanBeConvertedIntoBNB()
    type(var)
    len(var)
    var
    
    var = binance.dustTransfer()
    type(var)
    len(var)
    
    # var = binance.
    # type(var)
    # len(var)
    
    # var = binance.
    # type(var)
    # len(var)
