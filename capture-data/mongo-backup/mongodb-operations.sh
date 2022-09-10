#!/bin/bash
#####################################################################
#                                                                   #
# mongo --host 192.168.8.106 -u "admin" -p $mongodbadminpass
#                                                                   #
#                                                                   #
# if []                                                             #
# while -d:-r:                                                      #
#                                                                   #
# Add method for choose betweetn BACKUP or RESTORE.                 #
#                                                                   #
#####################################################################

#cd /home/llagask/Trading/polaris_beta/capture-data/mongo-backup
export databasename='binance_spot_margin_usdt'

######### BACKUP remote database (raspberry), locally #########
export databasename='binance_spot_margin_usdt' &&\
mongodump --gzip --uri="mongodb://admin:$mongodbadminpass@192.168.8.106:27017/$databasename?ssl=false&authSource=admin" dump/

#### --query #(query option requires pass a collection name)
#### --collection='collection_name_xxx'
#### --query='{ "timestamp": { "$lt": { "$date": "2022-06-28T00:00:00.000Z" } } }'

######### RESTORE DATABASE REMOTELY ##########
# mongorestore --gzip --host 192.168.8.106 --db binance_spot_margin_usdt \ 
# --authenticationDatabase="admin" -u "admin" -p $mongodbadminpass \ 
# --dir binance_spot_margin_usdt/ &> restoredb.log
