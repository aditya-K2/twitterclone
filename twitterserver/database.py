import mysql.connector
import os
import uuid
import bcrypt
# import json

GET_TIME_LINE_STATEMENT = '''( SELECT user_id, tweet_id, NULL as subtweet_id, tweet_body, time_posted FROM Tweets WHERE user_id in ( SELECT follows FROM followers WHERE user_id = "{user_id}" ))
                            UNION ( SELECT user_id, retweet_id, subtweet_id, retweet_body, time_posted FROM Retweets WHERE user_id in ( SELECT follows FROM followers WHERE user_id = "{user_id}" ))
                            UNION (( SELECT user_id, tweet_id, NULL as subtweet_id, tweet_body, time_posted FROM Tweets WHERE user_id = "{user_id}" )
                                    UNION ( SELECT user_id, retweet_id, subtweet_id, retweet_body, time_posted FROM Retweets WHERE user_id = "{user_id}" ))
                            ORDER BY time_posted DESC'''
GET_USER_TIME_LINE = '( SELECT user_id, tweet_id, NULL as subtweet_id, tweet_body, time_posted FROM Tweets WHERE user_id = "{user_id}" ) UNION ( SELECT user_id, retweet_id, subtweet_id, retweet_body, time_posted FROM Retweets WHERE user_id = "{user_id}" ) ORDER BY time_posted DESC'
GET_TWEET_TIME_LINE = 'SELECT * FROM Comments WHERE parent_tweet = "{tweet_id}" ORDER BY time_posted DESC'
GET_TWEET_STATMENT = '''( SELECT user_id, tweet_id, NULL as subtweet_id, tweet_body, time_posted FROM Tweets WHERE tweet_id = "{tweet_id}" )
                        UNION ( SELECT user_id, retweet_id, subtweet_id, retweet_body, time_posted FROM Retweets WHERE retweet_id = "{tweet_id}" )
                        UNION ( SELECT user_id, comment_id, NULL as subtweet_id, comment_body, time_posted FROM Comments WHERE comment_id = "{tweet_id}" ) ORDER BY time_posted DESC'''
GET_SINGLE_TWEET_STATMENT = '''( SELECT user_id, tweet_id, tweet_body, time_posted FROM Tweets WHERE tweet_id = "{tweet_id}" )
                        UNION ( SELECT user_id, retweet_id, retweet_body, time_posted FROM Retweets WHERE retweet_id = "{tweet_id}" )
                        UNION ( SELECT user_id, comment_id, comment_body, time_posted FROM Comments WHERE comment_id = "{tweet_id}" ) ORDER BY time_posted DESC'''
INSERT_TWEET_STATEMENT = 'INSERT INTO Tweets(user_id, tweet_id, tweet_body, time_posted) VALUES (%s,%s,%s, NOW())'
INSERT_COMMENT_STATEMENT = 'INSERT INTO Comments(user_id, comment_id, parent_tweet, comment_body, time_posted) VALUES (%s,%s,%s, %s, NOW())'
INSERT_RETWEET_STATEMENT = 'INSERT INTO Retweets(user_id, retweet_id, subtweet_id, retweet_body, time_posted) VALUES (%s,%s,%s, %s, NOW())'
GET_USER_STATEMENT = 'SELECT user_id, password FROM Users WHERE user_id = "{user_id}"'

NO_TWEET_ERROR = {
    "error" : "No Tweet"
}

SUCCESS_STATUS = {
    "status" : "successful addition of the user to database",
}

USER_ALREADY_EXISTS_ERROR = {
    "error" : "User Already Exists"
}

db = mysql.connector.connect(
        host=os.environ["TWITTER_DB_HOST"],
        user=os.environ["TWITTER_DB_USER"],
        passwd=os.environ["TWITTER_DB_PASSWORD"],
        database=os.environ["TWITTER_DB_NAME"])

def delete_tweet(tweet_id):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    cursor.execute('DELETE FROM Tweets WHERE tweet_id="{tweet_id}"'.format(tweet_id = tweet_id))
    db.commit()
    cursor.execute('DELETE FROM Retweets WHERE retweet_id="{tweet_id}" OR subtweet_id="{tweet_id}"'.format(tweet_id = tweet_id))
    db.commit()
    cursor.execute('DELETE FROM Comments WHERE comment_id="{tweet_id}" OR parent_tweet="{tweet_id}"'.format(tweet_id = tweet_id))
    db.commit()

def get_follow_relation(user_id, fo_id):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    cursor.execute('SELECT * from followers where user_id = "{user_id}" AND follows = "{fo_id}"'.format(user_id = user_id, fo_id = fo_id))
    res = cursor.fetchone()
    if res == None:
        return "Follow"
    else:
        return "Unfollow"

def follow(user_id, fo_id):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    if get_follow_relation(user_id, fo_id) == "Follow":
        val = (user_id, fo_id)
        cursor.execute('INSERT INTO followers(user_id, follows) VALUES(%s,%s)', val)
        db.commit()
        cursor.close()
    else:
        val = (user_id, fo_id)
        cursor.execute('DELETE FROM followers WHERE user_id="{user_id}" AND follows="{fo_id}"'.format(user_id = user_id, fo_id = fo_id))
        db.commit()
        cursor.close()

def insert_retweet(user_id, retweet_body, subtweet_id):
       tweet_id = uuid.uuid1()
       db.reconnect()
       cursor = db.cursor(buffered=True)
       val = (user_id, str(tweet_id), subtweet_id, retweet_body)
       cursor.execute(INSERT_RETWEET_STATEMENT, val)
       db.commit()
       cursor.close()

def check_user(user_id, passwd):
       db.reconnect()
       cursor = db.cursor(buffered=True)
       cursor.execute(GET_USER_STATEMENT.format(user_id = user_id))
       res = cursor.fetchone()
       if res == None:
           return False
       else:
            if bcrypt.checkpw(passwd.encode("utf-8"), res[1].encode("utf-8")):
                return True
            else:
                return False

def signin(user_id, passwd):
       hash = bcrypt.hashpw(passwd.encode("utf-8"), bcrypt.gensalt())
       db.reconnect()
       cursor = db.cursor(buffered=True)
       cursor.execute(GET_USER_STATEMENT.format(user_id = user_id))
       res = cursor.fetchone()
       if res == None:
           val = (user_id, hash)
           cursor.execute('INSERT INTO Users(user_id, password) VALUES(%s, %s)', val)
           cursor.close()
           db.commit()
           return True
       else:
           return False

def insert_comment(user_id, cb, parent_tweet_id):
       tweet_id = uuid.uuid1()
       db.reconnect()
       cursor = db.cursor(buffered=True)
       val = (user_id, str(tweet_id), parent_tweet_id, cb)
       cursor.execute(INSERT_COMMENT_STATEMENT, val)
       db.commit()
       cursor.close()

def insert_tweet(user_id: str, tweet_body: str):
       tweet_id = uuid.uuid1()
       db.reconnect()
       cursor = db.cursor(buffered=True)
       val = (user_id, str(tweet_id), tweet_body)
       cursor.execute(INSERT_TWEET_STATEMENT, val)
       db.commit()
       cursor.close()

def get_tweet(tweet_id: str):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    cursor.execute(GET_TWEET_STATMENT.format(tweet_id= tweet_id))

    res = cursor.fetchone()

    if res != None:
        if res[2] == None:
            return {
                "user_id" : res[0],
                "tweet_id" : res[1],
                "tweet_body" : res[3],
                "time_posted" : res[4].strftime("%m/%d/%Y, %H:%M:%S")
            }
        else:
            return {
                "user_id" : res[0],
                "tweet_id" : res[1],
                "subtweet_id" : get_single_tweet(res[2]),
                "tweet_body" : res[3],
                "time_posted" : res[4].strftime("%m/%d/%Y, %H:%M:%S")
            }

    else:
        return NO_TWEET_ERROR

def get_single_tweet(tweet_id):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    cursor.execute(GET_SINGLE_TWEET_STATMENT.format(tweet_id= tweet_id))

    res = cursor.fetchone()

    if res != None:
        return {
            "user_id" : res[0],
            "tweet_id" : res[1],
            "tweet_body" : res[2],
            "time_posted" : res[3].strftime("%m/%d/%Y, %H:%M:%S")
        }
    else:
        return NO_TWEET_ERROR

def get_user_time_line(user_id : str):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    cursor.execute(GET_USER_TIME_LINE.format(user_id= user_id))

    payload = []
    for tuple in cursor.fetchall():
        tweet = {}
        tweet["user_id"] = tuple[0]
        tweet["tweet_id"] = tuple[1]
        if tuple[2] != None:
            st = get_tweet(tuple[2])
            if st != NO_TWEET_ERROR:
                tweet["subtweet_id"] = st
        tweet["tweet_body"] = tuple[3]
        tweet["time_posted"] = tuple[4].strftime("%m/%d/%Y, %H:%M:%S")
        payload.append(tweet)

    return payload

def get_home_time_line(user_id : str):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    cursor.execute(GET_TIME_LINE_STATEMENT.format(user_id= user_id))

    payload = []
    for tuple in cursor.fetchall():
        tweet = {}
        tweet["user_id"] = tuple[0]
        tweet["tweet_id"] = tuple[1]
        if tuple[2] != None:
            st = get_tweet(tuple[2])
            if st != NO_TWEET_ERROR:
                tweet["subtweet_id"] = st
        tweet["tweet_body"] = tuple[3]
        tweet["time_posted"] = tuple[4].strftime("%m/%d/%Y, %H:%M:%S")
        payload.append(tweet)

    return payload

def get_tweet_time_line(tweet_id: str):
    db.reconnect()
    cursor = db.cursor(buffered=True)
    cursor.execute(GET_TWEET_TIME_LINE.format(tweet_id= tweet_id))

    payload = {}
    parent_tweet = get_tweet(tweet_id)
    if parent_tweet != NO_TWEET_ERROR:
        payload["tweet"] = parent_tweet
    else: return NO_TWEET_ERROR
    payload["comments"] = []
    for tuple in cursor.fetchall():
        comment = {}
        comment["comment_id"] = tuple[0]
        comment["parent_tweet_id"] = tuple[1]
        comment["user_id"] = tuple[2]
        comment["comment_body"] = tuple[3]
        comment["time_posted"] = tuple[4].strftime("%m/%d/%Y, %H:%M:%S")
        payload["comments"].append(comment)

    print(payload)
    return payload

get_tweet_time_line("b62fa5c0-c4f6-11ec-b539-a4c3f0c02461")
