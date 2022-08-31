from os import environ
import asyncio
from datetime import datetime

from binance import AsyncClient, BinanceSocketManager

from polaristools.mongodatabase import MongoDatabase
from polaristools.utils import logger_func, historicalKlinesParser


logger = logger_func(logger_name=__name__, filename='ws.log')

api_key = environ.get('binance_apikey')
api_secret = environ.get('binance_secretkey')

raspi = '192.168.8.106'
db_user = 'admin'
db_pass = environ.get('mongodbadminpass')

database_config = {'db_host':raspi,'db_user':db_user,'db_pass':db_pass,}
mongo = MongoDatabase(credentials=database_config)
client = mongo.mongoClient()


# def parse_persist_wsKline(data:dict, dbname:str, collection:str):
#     opentime = datetime.utcfromtimestamp(data['t']/1000)
#     closetime = datetime.utcfromtimestamp(data['T']/1000)
#     kline = {
#         'open_time':opentime,
#         'open':float(data['o']),
#         'high':float(data['h']),
#         'low':float(data['l']),
#         'close':float(data['c']),
#         'volume':float(data['v']),
#         'close_time':closetime,
#         'quote_asset_volume':float(data['q']),
#         'number_of_trades':int(data['n']),
#         'taker_buy_base_asset_volume':float(data['V']),
#         'taker_buy_quote_asset_volume':float(data['Q']),
#     }
    
#     # INSERT NEW DATA
#     created_id = mongo.insert_one_doc(
#         data = kline,
#         db_name = dbname,
#         collection = collection,
#     )
#     outputmsg = f'Mongodb ID: {created_id}'
#     return outputmsg

async def continuousklines(
                            symbol,
                            # db_name,
                            # collection_name,
                            persist=False,
                            ):
    client = await AsyncClient.create(api_key,api_secret) #Inizialize connection.
    bsm = BinanceSocketManager(client) #wraper function.
    
    # Coroutine.
    continuouskline_socket = bsm.kline_futures_socket(symbol)
    async with continuouskline_socket as socket_stream:
        while True:
            res = await socket_stream.recv()
            if persist:
                if res['k']['x']==True:
                    try:
                        msg = parse_persist_wsKline(
                            data=res['k'],
                            dbname = db_name,
                            collection = collection_name,
                        )
                        print(msg)
                    except Exception as e:
                        print(e)
            print(res['e'], res['ps'], res['k']['c'])
    
    await client.close_connection()

# futures_user_socket
async def usersocket(
                            # symbol,
                            # db_name,
                            # collection_name,
                            persist=False,
                            ):
    client = await AsyncClient.create(api_key,api_secret) #Inizialize connection.
    bsm = BinanceSocketManager(client) #wraper function.
    
    # Coroutine.
    userdata_socket = bsm.user_socket()
    async with userdata_socket as user_stream:
        while True:
            res = await user_stream.recv()
            
            print(res)
    
    await client.close_connection()

async def main():
    await asyncio.gather(
        # continuousklines(symbol='BNBUSDT'),
        # continuousklines(symbol='DOGEUSDT'),
        usersocket()
    )


if __name__== '__main__':
    
    # symbol='ETHUSDT'
    # interval='1m'
    # database_name = 'binance_spot_margin_busd_ejemplo'
    # collection = f'ws_klines_{symbol}_{interval}'
    
    asyncio.run(main())