# import bson

import configparser
import pymongo 
import os



#
# PyMongo Connection for Atlas
config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("sample1.ini")))
print(config['PROD']['DB_URI'])
client = pymongo.MongoClient(config['PROD']['DB_URI'])
db = client.get_database('FinAgent')
user_collection = pymongo.collection.Collection(db, 'user_collection')

def add_comment(movie_id, name, email, comment, date):

    comment_doc = { 'movie_id' : movie_id, 'name' : name, 'email' : email,'text' : comment, 'date' : date}
    return db.comments.insert_one(comment_doc)


def fin_user(phone_number,upi_id,user_ip,user_country,device_type):
    finagent_user={'phone_number': phone_number, 'upi_id': upi_id, 'user_ip':[user_ip],'user_country':[user_country],'device_type':[device_type]}
    return db.users.insert_one(finagent_user)

def fin_user_login(phone_number):
    return db.users.find_one({'phone_number':phone_number})

def fin_user_update(phone_number,user_ip,user_country,device_type):
    return db.user.update_one({'phone_number':phone_number},{ "$addToSet": { "user_ip": [user_ip],'user_country':[user_country],'device_type':[device_type]} })



def transaction_log(upi_id,transaction_id, transaction_amount, transaction_duration,user_ip,user_country,status, risk_score,device_type):
    transaction_log_user={'user_id':upi_id,'transaction_id':transaction_id,'transaction_amount':transaction_amount, 'transaction_duration':transaction_duration,'user_ip':user_ip,'user_country':user_country, 'status':status,'risk_score':risk_score,'device_type':device_type}
    return db.transaction.insert_one(transaction_log_user)

def transaction_status_update(trans_id,status):
    return db.transaction.update_one({'transaction_id':trans_id},{"$set":{'status':status}})


def transaction_risk_score_update(trans_id,risk_score):
    return db.transaction.update_one({'transaction_id':trans_id},{"$set":{'risk_score':risk_score}})

# def transaction_time_update(time_in_ms):
#     return db.transaction.update_one({'transaction_id':trans_id},{"$set":{'transaction_duration':time_in_ms}})

def transaction_log_find(trans_id):
    return db.transaction.find_one({'transaction_id':trans_id})

def all_transaction():
    return db.transaction.find()


def profile_transaction(upi_id):
    return db.transaction.find({'user_id':upi_id})


# if __name__ == "__main__":
#     app = create_app()
#     app.config['DEBUG'] = True
#     app.config['MONGO_URI'] = config['PROD']['DB_URI']

#     app.run()