RabbitMQ is a messaging broker that implemnts Advanced Message Queuing Protocol(AMQP).

The RabbitMQ mangement user interface is split between 6 tabs:

	Overview: Contains information regarding the total of queued messages, message rates, and global counts. Also contains information regarding the nodes, churn statistics, and information on the ports and contexts being used.  

	Connections: Contains the number of currently open client connections. This is important because you are able to monitor the connection opening/closure rates which will help you detect a large number of problems if they arise. 

	Channels: Contains the number of currently open channels and channel opening/closure rates. Remember channels cannot exist without a connection.

	Exchanges: Contains information regarding the exchanges where messages are sent. List information regarding the exchange like the name, type, features, message rate in, messgage rate out. 

	Queues: Contains information of all the queues. Also gives the user the option to add a new queue.

	Admin: Lists all users and gives the user the option to add additional users so they can gain access to the system. 


How to check to see if queues are being created:
	
	1. Navigate to the queue tabs in the rabbitmq UI after logging in.

	2. If the desired queue is shown in all queues, then that means the queue as been created.

	
	
