from datetime import datetime
import inspect
# import os
import pickle 
from time import time, sleep
from os import chdir, getcwd, listdir

import numpy as np
from pandas import DataFrame
import pdmongo
import talib

from polaristools.binanceconnection import BinanceConnection
from polaristools.mongodatabase import MongoDatabase
from polaristools.utils import *

''' 
    UNDER CONSTRUCTION.
    '''

class PolarisBot:

    def __init__(self, mongo_cred={}, **kwargs):
        ''' 
            '''
        self.binance = BinanceConnection()
        
        if mongo_cred:
            credentials = dict(
                db_host = mongo_cred.get('db_host'),
                db_user = mongo_cred.get('db_user'),
                db_pass = mongo_cred.get('db_pass'),
            )
            try:
                self.mongo = MongoDatabase(credentials)
                self.mongo_client = self.mongo.mongoClient()
                print(35*'#','\n# Module PolarisBot initialized.  #\n# Mongo Database available now.\t  #\n',35*'#','\n')
            except:
                print('# *** Something goes wrong dude. *** #')
        # else:
            # print('No credentials passed yet')

    def createDatabaseKlines(self,symbols:list,interval:str,quoted_asset:str,stream_type:str,market_type:str,):
        logger = logger_func(logger_name=__name__, filename='file.log')
        testConn = self.mongo.pingServer()
        if testConn == 400:
            return 'MongoServer is NOT available\n'
        ms_now              = int(time()*1000)
        db_name             = f"binance_{market_type}_{quoted_asset}"
        limit               = 500
        timeframe:int       = interval_to_milliseconds(interval)
        last_valid_ms:int   = latest_valid_timestamp(timeframe)
        for symbol in symbols:
            collection_name = f"{stream_type}_{symbol.upper()}_{interval.lower()}"
            start_ms:int    = self.binance.getEarliestValidTimestamp(symbol, interval, stream_type)
            while True:
                if stream_type=='klines':
                    temp_data = self.binance.klineCandlestick(
                        symbol = symbol,
                        interval = interval,
                        startTime = start_ms,
                        endTime = last_valid_ms,
                        limit = limit,
                    )
                elif stream_type=='continuous_klines':
                    temp_data = self.binance.futuresContinuousKlines(
                        pair = symbol,
                        interval = interval,
                        startTime = start_ms,
                        endTime = last_valid_ms,
                        limit = limit,
                    )
                else:
                    print('Wrong parameters', inspect.currentframe().f_code.co_name)
                    break
                if not temp_data:
                    logger.warning('Empty data returned from: %s %s'%(symbol,interval))
                    break
                firstdata = datetime.utcfromtimestamp(temp_data[0][0]/1000)
                lastdata = datetime.utcfromtimestamp(temp_data[-1][0]/1000)
                logger.warning('DATA FETCHED # symbol: %s chuncksize: %d start time: %s end time: %s '%\
                    (symbol, len(temp_data), firstdata, lastdata))
                dataframe = historicalKlinesParser(temp_data)
                my_db = self.mongo_client[db_name]
                ptm = pdmongo.to_mongo(
                    frame     = dataframe,
                    name      = collection_name,
                    db        = my_db,
                    if_exists = 'append',
                )
                logger.warning('# A new collection: %s has been append to database: %s'% \
                    (collection_name,db_name))
                start_ms = temp_data[-1][0] + timeframe
                if (temp_data[-1][0]) >= last_valid_ms:
                    logger.warning('Last valid open_time kline has been reached')
                    print('\n')
                    break
                sleep(2)
        logger.warning('New Database created successfully')
        print('\n')

    def updateDatabaseKlines(self,symbols:list,interval:str,quoted_asset:str,stream_type:str,market_type:str,):
        logger = logger_func(logger_name=__name__, filename='file.log')
        testConn = self.mongo.pingServer()
        if testConn == 400:
            return 'MongoServer is not available\n'
        ms_now            = int(time()*1000)
        db_name           = f"binance_{market_type}_{quoted_asset}"
        timeframe:int     = interval_to_milliseconds(interval)
        last_valid_ms:int = latest_valid_timestamp(timeframe)
        for symbol in symbols:
            collection_name = f"{stream_type}_{symbol.upper()}_{interval.lower()}"
            try:
                newest_entry = self.mongo.extractNewestDate(db_name, collection_name)
                newest_ms = int(newest_entry.timestamp()*1000)
                logger.warning('The Newest entry stored is: %s'%newest_entry)
            except:
                logger.warning('Database or collection seems does not exists')
                print('\n')
                # In a continuous execution environment you don't want to Return the function.
                # return
                continue
            difference = last_valid_ms - newest_ms
            if difference < timeframe:
                logger.warning('Newest valid data stored yet for collection: %s'%collection_name)
                print('\n')
                continue
            start_ms = (newest_ms + timeframe)
            while True:
                if stream_type=='klines':
                    temp_data = self.binance.klineCandlestick(
                        symbol = symbol,
                        interval = interval,
                        startTime = start_ms,
                        endTime = last_valid_ms,
                    )
                elif stream_type=='continuous_klines':
                    temp_data = self.binance.futuresContinuousKlines(
                        pair = symbol,
                        interval = interval,
                        startTime = start_ms,
                        endTime = last_valid_ms,
                    )
                else:
                    print('Wrong parameters', inspect.currentframe().f_code.co_name)
                    break
                if not temp_data:
                    logger.warning('Empty data returned from: %s %s'%(symbol,interval))
                    print('\n')
                    break
                firstdata = datetime.utcfromtimestamp(temp_data[0][0]/1000)
                lastdata = datetime.utcfromtimestamp(temp_data[-1][0]/1000)
                logger.warning('DATA FETCHED # symbol: %s chuncksize: %d start time: %s end time: %s '%\
                    (symbol, len(temp_data), firstdata, lastdata))
                dataframe = historicalKlinesParser(temp_data)
                my_db = self.mongo_client[db_name]
                ptm = pdmongo.to_mongo(
                    frame     = dataframe,
                    name      = collection_name,
                    db        = my_db,
                    if_exists = 'append')
                logger.warning('# UPDATED database %s  in collection -> %s '%\
                    (db_name, collection_name))
                start_ms = temp_data[-1][0] + timeframe
                if (temp_data[-1][0]) >= last_valid_ms:
                    logger.warning('Last valid open_time kline has been reached')
                    print('\n')
                    break
                sleep(2) # Be gentle with the server, avoid ban.
        logger.warning('##### ##### ##### Databases UPDATED successfully ##### ##### #####')
        print('\n')

    def verifyDatasetDatesIntegrity(self):
        ''' 
            Método que analiza la columna de open_time como un array,
            buscando repeticiones y discontinuidad de las fechas.
            '''
        pass

    def createDataframe(
                        self,
                        mydb:str,
                        collection:str,
                        date_range:dict={},
                        limit_output:int=1e7,
                        index_col:str='open_time',
                        ):
        ''' 
            date_range: {gt:datetime(2020,1,1,0,0)} 
            
            '''
        project_fields={
            '$project':
                {
                    '_id' :0,
                    'open_time' :1,
                    'open' :1,
                    'high' :1,
                    'low' :1,
                    'close' :1,
                    'volume' :1,
                }
        }
        if date_range:
            match_date_range = {
                '$match':{
                    index_col:{
                        '$gt':date_range['gt'],
                        # '$lte':date_range['lte']
                    }
                }
            }
        else: 
            match_date_range = {'$match':{}}
        df = pdmongo.read_mongo(
            db          = self.mongo_client[mydb],
            collection  = collection,
            query       = [
                project_fields,
                match_date_range,
                {'$limit':limit_output},
            ], 
            index_col   = [index_col],
        )
        return df

    def addIndicators(self,df:DataFrame,indicators:dict):
        if not indicators:
            print('No indicators added !')
            return df
        for indicator in indicators.keys():
            if indicator=='simple_returns':
                lookback = indicators[indicator].get('lookback', 1)
                df['simple_returns'] = df.close.pct_change(lookback)
            elif indicator=='log_returns':
                lookback = indicators[indicator].get('lookback', 1)
                df['log_returns'] = np.log(1 + df.close.pct_change(lookback))
            elif indicator=='talib_EMA':
                for period in indicators[indicator]:
                    colname = f'talib_EMA_{period}'
                    df[colname] = talib.EMA(df.close, timeperiod=period)
            elif indicator=='talib_ATR':
                timeperiod = indicators[indicator].get('timeperiod', 14)
                df['talib_ATR'] = talib.ATR(df.high.copy(), df.low.copy(), df.close.copy(), timeperiod=timeperiod)
            elif indicator=='talib_SAR':
                acceleration = indicators[indicator].get('acceleration', 0.02)
                maximum = indicators[indicator].get('maximum', 0.2)
                df['talib_SAR'] = talib.SAR(df.high.copy(), df.low.copy(), acceleration=acceleration, maximum=maximum)
            elif indicator=='talib_BBANDS':
                timeperiod = indicators[indicator].get('timeperiod', 5)
                nbdevup = indicators[indicator].get('nbdevup', 2)
                nbdevdn = indicators[indicator].get('nbdevdn', 2)
                matype = indicators[indicator].get('matype', 0)
                df['BB_up'],df['BB_mid'],df['BB_low'] = talib.BBANDS(
                    df.close.copy(), timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype
                )
            elif indicator=='talib_STOCHRSI':
                timeperiod = indicators[indicator].get('timeperiod', 14)
                fastk_period = indicators[indicator].get('fastk_period', 5)
                fastd_period = indicators[indicator].get('fastd_period', 3)
                fastd_matype = indicators[indicator].get('fastd_matype', 0)
                df['talib_STOCHRSI_k'], df['talib_STOCHRSI_d'] = talib.STOCHRSI(
                    df.close, timeperiod=timeperiod, 
                    fastk_period=fastk_period, fastd_period=fastd_period, fastd_matype=fastd_matype,
                )                
            elif indicator=='talib_MACD':
                fastperiod = indicators[indicator].get('fastperiod', 12)
                slowperiod = indicators[indicator].get('slowperiod', 26)
                signalperiod = indicators[indicator].get('signalperiod', 9)
                df['talib_MACD'], df['talib_MACD_signal'], df['talib_MACD_hist'] = talib.MACD(
                    df.close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod
                ) 
            elif indicator=='talib_ADX':
                timeperiod = indicators[indicator].get('timeperiod', 14)
                df['talib_ADX'] = talib.ADX(df.high, df.low, df.close, timeperiod=timeperiod)
            elif indicator=='talib_RSI':
                timeperiod = indicators[indicator].get('timeperiod', 14)
                df['talib_RSI'] = talib.RSI(df.close, timeperiod=timeperiod)
            elif indicator=='talib_AROON':
                timeperiod = indicators[indicator].get('timeperiod', 14)
                df['talib_AROON_down'], df['talib_AROON_up'] = talib.AROON(
                    df.high, df.low, timeperiod=timeperiod
                )
            elif indicator=='talib_OBV':
                df['talib_OBV'] = talib.OBV(df.close, df.volume)
            elif indicator=='talib_doji':
                df['talib_doji'] = talib.CDLDOJI(df.open, df.high, df.low, df.close)
        return df

    def _find_directory(target_dir):
        def decorator_a(function): # <funcion> va a ser decorada.
            def wrapper_func(self, *args, **kwargs): #función que ejecuta la función objetivo.
                deep=5
                orig_dir=getcwd()
                while deep:
                    if not target_dir in listdir():
                        chdir('../')
                        deep-=1
                    else:
                        dataframe = function(self, *args, **kwargs) #Dada la condición decorada.
                        chdir(orig_dir)
                        return dataframe
            return wrapper_func
        return decorator_a
    
    @_find_directory(target_dir='datasets')
    def dataframeToBinary(self,dataframe:DataFrame,filename:str): 
        try: 
            filepath = f"datasets/{filename}.pckl"
            with open(filepath, 'wb') as bin_df:
                pickle.dump(dataframe, bin_df)
            print(f'{filename} persisted as binary ok')
        except Exception as e:
            print(f"{e}\nfrom:{inspect.currentframe().f_code.co_name}")

    @_find_directory(target_dir='datasets')
    def dataframeFromBinary(self,filename:str):
        try:
            filepath = f"datasets/{filename}.pckl"
            with open(filepath, 'rb') as df_bin:
                dataframe = pickle.load(df_bin)
                return dataframe
        except:
            print("Requested file does not exists yet")

    def checkWallet(self, market_type):
        return self.binance.dailyAccountSnapshot(type=market_type)

    def checkDatabaseConnection(self):
        pass

    def checkOpenOrders(self):
        pass

    def startJournal(self):
        pass

    def checkPositions(self):
        currentOpenOrdersList = self.binance.currentOpenOrders()
        open_ord = len(currentOpenOrdersList) 
        if open_ord == 0:
            return 'Open Orders: 0'
        else:
            return f'Open Orders: {open_ord}'

    def buildStack(self):
        self.checkWallet()
        self.checkDatabase()
        self.checkOpenOrders()


if __name__== '__main__':
    
    from polaristools.polarisbot import PolarisBot
    from os import environ
    
    raspi = '192.168.8.106'
    db_user = 'admin'
    db_pass = environ.get('mongodbadminpass')
    
    polaris = PolarisBot()
    
    df = polaris.dataframeFromBinary(filename='df_klines_BTCUSDT_1d')
    df.tail()
    
    database_config = {
        'db_host':raspi,
        'db_user':db_user,
        'db_pass':db_pass,
    }
    polaris = PolarisBot(mongo_cred=database_config)
    polaris = PolarisBot()
    
    wallet_spot = polaris.checkWallet(market_type='SPOT')
    wallet_fusd = polaris.checkWallet(market_type='FUTURES')

    polaris.checkPositions()
    
    df = polaris.dataframeFromBinary(filename='df_klines_BTCUSDT_1d')
    df.tail()
    
    df = polaris.dataframeFromBinary(filename='df_klines_ETHUSDT_1d')
    df.tail()
    df_nan = df[:-1]
    polaris.dataframeToBinary(dataframe=df_nan, filename='df_klines_ETHUSDT_1d')

    type(df.isnull().sum().sum())
    
    df = polaris.dataframeFromBinary(filename='df_klines_BNBUSDT_1d')
    df.tail()
    df_nan = df[:-1]
    polaris.dataframeToBinary(dataframe=df_nan, filename='df_klines_BNBUSDT_1d')
    
    df = polaris.dataframeFromBinary(filename='df_klines_DOGEUSDT_1d')
    df.tail()
    df_nan = df[:-1]
    polaris.dataframeToBinary(dataframe=df_nan, filename='df_klines_DOGEUSDT_1d')