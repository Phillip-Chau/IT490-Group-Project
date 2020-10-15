import pika
import mysql.connector
import os
import time
import logging
import json 
import time
from mysql.connector import errorcode

def process_request(ch, method, properties, body):
    """
    Gets a request from the queue, acts on it, and returns a response to the
    reply-to queue
    """
    request = json.loads(body)
    if 'action' not in request:
        response = {
            'success': False,
            'message': "Request does not have action"
        }
    else:
        action = request['action']
        if action == 'GETHASH':
            data = request['data']
            email = data['email']
            logging.info(f"GETHASH request for {email} received")
            curr.execute('SELECT hash FROM users WHERE email=%s;', (email,))
            row =  curr.fetchone()
            if row == None:
                response = {'success': False}
            else:
                response = {'success': True, 'hash': row[0]}
        elif action == 'REGISTER':
            data = request['data']
            email = data['email']
            hashed = data['hash']
            logging.info(f"REGISTER request for {email} received")
            curr.execute('SELECT * FROM users WHERE email=%s;', (email,))
            if curr.fetchone() != None:
                response = {'success': False, 'message': 'User already exists'}
            else:
                curr.execute('INSERT INTO users VALUES (%s, %s);', (email, hashed))
                conn.commit()
                response = {'success': True}
        else:
            response = {'success': False, 'message': "Unknown action"}
    logging.info(response)
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(response)
    )

print("Giving db a chance to start...")
time.sleep(20)

cnx = None
try:
  print("Signing in to database...")
  cnx = mysql.connector.connect(user='root', password='example', host='db', database='users')
  print(f"Success: {cnx}")
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with your user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)

print("Testing a query...")
cursor = cnx.cursor()
cursor.execute("SELECT * FROM user")
for row in cursor:
  print(row)

print("Back End Is Running Now")
