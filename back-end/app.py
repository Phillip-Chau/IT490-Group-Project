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
            curr_r.execute('SELECT hash FROM user WHERE name=%s;', (name,))
            row =  curr_r.fetchone()
            if row == None:
                response = {'success': False}
            else:
                response = {'success': True, 'hash': row[0]}
        elif action == 'REGISTER':
            data = request['data']
            name = data['name']
            hashed = data['hash']
            logging.info(f"REGISTER request for {name} received")
            curr_r.execute('SELECT * FROM user WHERE name=%s;', (name,))
            if curr_r.fetchone() != None:
                response = {'success': False, 'message': 'User already exists'}
            else:
                curr_rw.execute('INSERT INTO user VALUES (%s, %s);', (name, hashed))
                cnx_rw.commit()
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
cnx_r = None
cnx_rw = None
while True:
    logging.info(f"Waiting {wait_time}s...")
    time.sleep(wait_time)
    if wait_time < 60:
        wait_time = wait_time * 2
    else:
        wait_time = 60
    try:
        logging.info("Connecting to the read-only database...")
        postgres_password = os.environ['POSTGRES_PASSWORD']
        cnx_r = mysql.connector.connect(user='postgres', password=postgres_password, host='db-r', database='example')
        logging.info(f"Success: {cnx_r}")
        logging.info("Connecting to the read-write database...")
        postgres_password = os.environ['POSTGRES_PASSWORD']
        cnx_rw = mysql.connector.connect(user='postgres', password=postgres_password, host='db-rw', database='example')
        logging.info(f"Success: {cnx_rw}")
        logging.info("connecting to messaging service...")
        credentials = pika.PlainCredentials(
	      os.environ['RABBITMQ_DEFAULT_USER'],
              os.environ['RABBITMQ_DEFAULT_PASS']
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


logging.info("Back End Is Running Now")

logging.info("Starting consumption...")
channel.start_consuming()

