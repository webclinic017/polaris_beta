from bson.objectid import ObjectId
import inspect
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import pytz


class MongoDatabase:
    
    def __init__(self,credentials):
        
    
        self.db_user = credentials.get('db_user')
        self.db_pass = credentials.get('db_pass')
        self.db_host = credentials.get('db_host')
        
        if credentials.get('db_name'):
            self.db_name = credentials.get('db_name')
            self.my_db = self.client[self.db_name]
        if credentials.get('collection_name'):
            self.collection_name = credentials.get('collection_name')
        
        try:
            uri = f'mongodb://{self.db_user}:{self.db_pass}@{self.db_host}'
            self.client = MongoClient(uri)
            self.client.admin.command('ping')
            print(f'MongoDB server. host : {self.db_host}\n')
        except ConnectionFailure:
            print('MongoDB server NOT fetched\n')

    def mongoClient(self):
        return self.client

    def pingServer(self)->int():
        try:
            self.client.admin.command('ping')
            # print('MongoDB server is available')
            server_status = 200
        except ConnectionFailure:
            # print('MongoDB server is not available')
            server_status = 400
        return server_status

    def showDatabases(self):
        return self.client.list_database_names()
        
    def showCollections(self, **kwargs):
        if kwargs.get('db_name'):
            db_name = kwargs.get('db_name')
            my_db = self.client[db_name]
        else:
            my_db = self.client[self.db_name]
        return my_db.list_collection_names()

    def readEdges(self, db_name:str, collection:str):
        my_db           = self.client[db_name]
        query_startdate = my_db[collection].find().sort('open_time',1).limit(1)
        query_enddate   = my_db[collection].find().sort('open_time',-1).limit(1)
        startdate       = query_startdate.next()['open_time']
        enddate         = query_enddate.next()['open_time']
        # print('start date: ',startdate,'\n','end date: ',enddate)
        return (startdate,enddate)

    def extractNewestDate(self, db_name:str, collection:str):
        my_db = self.client[db_name]
        try:
            query_newest = my_db[collection].find().sort('open_time',-1).limit(1)
            dtime = (query_newest.next()['open_time']).replace(tzinfo=pytz.utc)
            return dtime
        except:
            print(f'Parece que la base de datos {db_name} o colección {collection} no han sido creadas aún. {inspect.currentframe().f_code.co_name}')

    def deleteNewestEntry(self, db_name:str, collection:str):
        my_db   = self.client[db_name]
        query_last = my_db[collection].find().sort('open_time',-1).limit(1)
        last_doc = query_last.next()
        my_db[collection].delete_one( {'_id':ObjectId(last_doc['_id'] )} )
        return last_doc['_id']

    def delete_many(self, db_name:str, collection:str, query:dict):
        my_db          = self.client[db_name]
        my_db[collection].delete_many(query)
        return 'deleted'
        
    def insert_one_doc(self, db_name:str, collection:str, data:dict):
        """
            Insert data into mongoDB
            """
        my_db = self.client[db_name]
        coll = my_db[collection]
        created_id = coll.insert_one(data).inserted_id
        return created_id

    def countDocuments(self, db_name, collection):
        my_db = self.client[db_name]
        collection = my_db[collection]
        return collection.count_documents(filter={})
    
    def dropCollection(self, db_name, collection):
        my_db = self.client[db_name]
        collection = my_db[collection]
        collection.drop()
        print(f'Collection: {collection} dropped !.')
    
    def dropDatabase(self, db_name):
        self.client.drop_database(db_name)
        print('Dropped database :',db_name)

if __name__== '__main__':
    
    from polaristools.mongodatabase import MongoDatabase
    from os import environ
    
    
    credentials = dict(
        db_user = 'admin',
        db_pass = environ.get('mongodbadminpass'),
        db_host = '192.168.8.106',
    )
    
    mongo = MongoDatabase(credentials)
    
    # db_name='binance_spot_margin_usdt
    
    mongo.showDatabases()
    mongo.showCollections(db_name='binance_spot_margin_usdt')
    # mongo.showCollections(db_name='binance_futures_usds_md')
    
    mongo.readEdges(db_name='binance_spot_margin_usdt', collection='klines_BTCUSDT_1d')
    
    newest_entry = mongo.extractNewestDate(
        db_name='binance_spot_margin_usdt', collection='klines_AVAXUSDT_1d'
    )
    type(newest_entry)
    print(newest_entry)
    dir(newest_entry)
    newest_entry.timestamp()
    
    # print(mongo.deleteNewestEntry(db_name='binance_spot_margin_marketdata', collection='klines_SOLUSDT_1d'))
    # print(mongo.extractNewestDate(db_name='binance_spot_margin_marketdata', collection='klines_SOLUSDT_1d'))
    # print(mongo.extractNewestDate(db_name='binance_spot_margin_marketdata', collection='klines_BTCUSDT_1h'))
    
    from datetime import datetime
    query = {
            'open_time' :{
                        '$gt' : datetime(2022,5,1,0,0,0),
                        # '$lt' : datetime(2021,11,1,0,0,0)
                        } 
            }
    mongo.delete_many(
                    db_name='binance_spot_margin_marketdata', 
                    collection='klines_BTCUSDT_1h',
                    query=query
                    )
                    
    mongo.pingServer()