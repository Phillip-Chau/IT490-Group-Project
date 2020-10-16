FROM mysql:latest
ENV MYSQL_ROOT_PASSWORD=example
ENV MYSQL_DATABASE=users
ENV MYSQL_USER=tester1
ENV MYSQL_PASSWORD=pwsd

ADD aCode.sql /docker-entrypoint-initdb.d/
