import pika
import mysql.connector

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
cnx = mysql.connector.connect(user='tester1', password='pwsd',
                              host='localhost',
                              database='users')
cnx.close()
print("Back End Is Running Now")
