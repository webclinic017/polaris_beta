import asyncio
import os

from binance import AsyncClient, BinanceSocketManager

from polaristools.mongodatabase import MongoDatabase

''' 
    UNDER CONSTRUCTION
    '''

mongo = MongoDatabase()
db_name='binance_spot_margin_marketdata'
collection='binance_userdata_streams'


async def binanceuserdatastream():
    client = await AsyncClient.create(
                                    api_key=os.environ.get('binance_apikey'),
                                    api_secret = os.environ.get('binance_secretkey')
                                    )
    bm = BinanceSocketManager(client)
    userdata = bm.user_socket()

    async with userdata as user_cm:
        while True:
            response = await user_cm.recv()
            print(response)
            output = mongo.insert_one_doc(
                                        db_name=db_name, 
                                        collection=collection,
                                        data=response
                                        )
            print(output)
    await client.close_connection()


if __name__== '__main__':
    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(binanceuserdatastream())
    
    ''' 
        bm.futures_user_socket()
        
        '''