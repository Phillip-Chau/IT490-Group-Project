import pika
import json
import time
import logging
import os

class Messaging:
    request_queue_name = 'request'

    credentials = pika.PlainCredentials(os.environ['RABBITMQ_DEFAULT_USER'],
                                        os.environ['RABBITMQ_DEFAULT_PASS'])

    host = 'messaging'

    def __init__(self):
        logging.info("Messaging: Establishing connection")
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, credentials=self.credentials))
        self.channel = self.connection.channel()
        logging.info("Messaging: Creating queues")
        self.channel.queue_declare(queue=self.request_queue_name)
        self.result_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue

    def __del__(self):
        logging.info("Messaging: Closing down connection")
        self.connection.close()

    def send(self, action, data):
        logging.info(f"Messaging: send(action={action}, data={data})")

        self.channel.basic_publish(
            exchange='',
            routing_key=self.request_queue_name,
            properties=pika.BasicProperties(
                reply_to=self.result_queue),
                body=json.dumps({'action': action, 'data': data}
            )
        )

    def receive(self):
        attempts = 0
        while True:
            method_frame, properties, body = self.channel.basic_get(
                self.result_queue, auto_ack=True)
            if method_frame:
                received = json.loads(body)
                logging.info(f"Messaging: received={received}")
                return received
            elif attempts > 10:
                logging.info("Messaging: receive did not get message") 
                return None 
            else:
                time.sleep(0.1)
                attempts += 1