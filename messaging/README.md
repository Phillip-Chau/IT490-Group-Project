# How to use RabbitMQ Management

## What is required in the .yml file?

messaging:
   image: 'rabbitmq:3.8.8-management'
   ports:
       - 15672:15672

The management version must be specified, rabbitmq also requires to be forwarded to port 15672.

## How to get to the web interface?

After it is confirmed to be running, you can access the web interface by typing 'http://localhost:15672' within your web browser.

## What is displayed on the web interface?

Overview: Contains information regarding the total of queued messages, message rates, and global counts. Also contains information regarding the nodes, churn statistics, and information on the ports and contexts being used.  

	Connections: Contains the number of currently open client connections. This is important because you are able to monitor the connection opening/closure rates which will help you detect a large number of problems if they arise. 

	Channels: Contains the number of currently open channels and channel opening/closure rates. Remember channels cannot exist without a connection.

	Exchanges: Contains information regarding the exchanges where messages are sent. List information regarding the exchange like the name, type, features, message rate in, messgage rate out. 

	Queues: Contains information of all the queues. Also gives the user the option to add a new queue.

	Admin: Lists all users and gives the user the option to add additional users so they can gain access to the system. 
