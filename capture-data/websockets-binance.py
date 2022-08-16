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

mongo = MongoDatabase(**database_config)

client = mongo.mongoClient()

def parse_persist_wsKline(
    data:dict,
    db_name = 'binance_spot_margin_busd_ejemplo',
    p_collection = 'ws_klines_BTCUSDT_1m',
    ):
    opentime = datetime.utcfromtimestamp(data['t']/1000)
    closetime = datetime.utcfromtimestamp(data['T']/1000)
    kline = {
        'open_time':opentime,
        'open':float(data['o']),
        'high':float(data['h']),
        'low':float(data['l']),
        'close':float(data['c']),
        'volume':float(data['v']),
        'close_time':closetime,
        'quote_asset_volume':float(data['q']),
        'number_of_trades':int(data['n']),
        'taker_buy_base_asset_volume':float(data['V']),
        'taker_buy_quote_asset_volume':float(data['Q']),
    }
    # INSERT NEW DATA
    created_id = mongo.insert_one_doc(
        db_name=db_name,
        collection=p_collection,
        data=kline
    )
    outputmsg = f'Mongodb ID: {created_id}'
    return outputmsg

async def main(persist=False):
    client = await AsyncClient.create(api_key,api_secret)
    bm = BinanceSocketManager(client)
    ks = bm.kline_socket('BTCUSDT', interval='1m')
    # ks = bm.kline_socket('BNBBTC', interval='1m')

    async with ks as tscm:
        while True:
            res = await tscm.recv()
            if res['k']['x']==True:
                print('***** ***** *****Kline closed ***** ***** *****')
                msg = parse_persist_wsKline(data=res['k'])
                print(msg)
                print('***** ***** *****Kline closed ***** ***** *****')
            
            print(res)
    await client.close_connection()


if __name__== '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())