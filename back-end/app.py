import pika
import mysql.connector
import os
import time
import logging
import json 
import time
from mysql.connector import errorcode

def process_request(ch, method, properties, body):

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
            name = data['name']
            logging.info(f"GETHASH request for {name} received")
            curr.execute('SELECT password FROM users WHERE name=%s;', (name,))
            row =  curr.fetchone()
            if row == None:
                response = {'success': False}
            else:
                response = {'success': True, 'password': row[0]}
        elif action == 'REGISTER':
            data = request['data']
            name = data['name']
            password = data['password']
            logging.info(f"REGISTER request for {name} received")
            curr.execute('SELECT * FROM users WHERE name=%s;', (name,))
            if curr.fetchone() != None:
                response = {'success': False, 'message': 'User already exists'}
            else:
                curr.execute('INSERT INTO users VALUES (%s, %s);', (name, password))
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

logging.basicConfig(level=logging.INFO)

logging.info("Giving db a chance to start...")
time.sleep(20)
wait_time = 1
cnx = None
while True:
    logging.info(f"Waiting {wait_time}s...")
    time.sleep(wait_time)
    if wait_time < 60:
        wait_time = wait_time * 2
    else:
        wait_time = 60
    try:
        logging.info("Connecting to the database...")
        logging.info("Signing in to database...")
        cnx = mysql.connector.connect(user='root', password='example', host='db', database='users')
        logging.info(f"Success: {cnx}")
        logging.info("connecting to messaging service...")
        credentials = pika.PlainCredentials(
	      'guest',
	      'guest'
	)
        connection = pika.BlockingConnection(
	      pika.ConnectionParameters(
	    	      host='messaging',
		      credentials=credentials
		)  
	)

        break
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
          logging.info("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
          logging.info("Database does not exist")
        else:
          logging.info(err)
    except pika.exceptions.AMQPConnectionError:
        logging.info("Unable to connect to messaging.")
        continue
curr = cnx.cursor()
channel = connection.channel()

channel.queue_declare(queue='request')

channel.basic_consume(queue='request', auto_ack=True,
                      on_message_callback=process_request)

logging.info("Testing a query...")
curr.execute('INSERT INTO user VALUES ("Kurt");')
cursor = cnx.cursor()
cursor.execute("SELECT * FROM user")
for row in cursor:
  logging.info(row)

logging.info("Back End Is Running Now")

logging.info("Starting consumption...")
channel.start_consuming()

