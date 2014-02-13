import os


## Environment
environment = os.environ.get('ENVIRONMENT', 'test')

## Database
global mongo

if environment == 'test':
    global mongo
    import mongomock as mongo
else:
    global mongo
    import pymongo as mongo

db_uri = os.environ.get('MONGOLAB_URI', 'mongodb://localhost')
db_name = os.environ.get('MONGOLAB_DB', 'whiskeynode')
db = mongo.MongoClient(db_uri)[db_name]
