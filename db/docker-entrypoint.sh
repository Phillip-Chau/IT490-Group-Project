#!/bin/bash

function find_primary() {
    PRIMARY=""
    for NODE in $MYSQL_NODES; do
        NODE_IP=$( dig +short $NODE )
        if [ -z $NODE_IP] || [ $NODE_IP != $MY_IP]; then
            EXIT_CODE=0
            pg_isready -h $NODE || EXIT_CODE=$?
            if [ $EXIT_CODE -eq 0 ]; then
                #need to find replacement for pgpass
                echo "$NODE:5432:mysql:mysql:$MYSQL_PASSWORD" >> ~/.pgpass
                VALUE=$(psql -U postgres -t -h $NODE -d postgres -c "select pg_is_in_recovery()")
                if [ $VALUE == "f" ]; then
                    echo "$NODE is primary node"
                    if [ ! -z $PRIMARY ]; then
                        echo "Two primary nodes detected! Exiting..."
                        exit 1
                    fi
                    PRIMARY=$NODE
                fi
            fi
        fi
    done
}
# end::find_primary[]

if [ -z $MYSQL_NODES ]; then
    echo "This image will not start without MYSQL_NODES defined."
    exit 1
fi
if [ -z $MYSQL_PASSWORD ]; then
    echo "This image will not start without MYSQL_PASSWORD defined."
    exit 1
fi
if [ -z $MYSQL_REPLICA_PASSWORD ]; then
    echo "This image will not start without MYSQL_REPLICA_PASSWORD defined."
    exit 1
fi

# tag::monitor[]
function monitor() {
    while true; do
        # spread out our checks to avoid the chance of two nodes promoting at
        # the same time
        WAIT=$((20 + $RANDOM % 10))
        sleep $WAIT
        find_primary
        if [ -z $PRIMARY ]; then
            echo "Can't find a primary failing over..."
            pg_ctl promote
            # we don't need to monitor any more if we are the primary
            exit
        fi
    done
}
# end::monitor[]

if [ "$(id -u)" = '0' ]; then
    exec gosu mysql "$BASH_SOURCE" "$@"
fi

# WOnt work cause pgpass is for postgres
touch ~/.pgpass
chmod 600 ~/.pgpass

# Start by looking for a primary node, we need our IP so we don't check
# ourselves
MY_IP=$( dig +short `hostname`)
find_primary

# The first node in the list gets a bit of a head start in case everything
# was brough up at once. This prevents a race to become the primary.
FIRST_IP=$( dig +short `echo $MYSQL_NODES | cut -d \  -f 1`)
if [ $MY_IP != $FIRST_IP ] && [ -z $PRIMARY ]; then
    echo "Giving the first node a 10s head start..."
    sleep 10
    find_primary
fi

if [ -z $PRIMARY ]; then
    # tag::configure_primary[]
    echo "Configuring a PRIMARY instance..."

    if [ -s "$MSDATA/MS_VERSION" ]; then
        echo "Database already exists, NOT creating a new one"
    else
        echo "Creating a new database..."

        initdb --username=mysql --pwfile=<(echo "$MYSQL_PASSWORD")

        # Start a temporary server listening on localhost
        pg_ctl -D "$MSDATA" -w start

        # Create a user for replication operations
        psql -v ON_ERROR_STOP=1 --username "$MYSQL_USER" --dbname "$MYSQL_DB" << EOSQL
            CREATE USER repuser REPLICATION LOGIN ENCRYPTED PASSWORD '$MYSQL_REPLICA_PASSWORD';
EOSQL

        # Stop the temporary server
        pg_ctl -D "$MSDATA" -m fast -w stop

        # Set up authentication parameters
        echo "host replication all all md5" >> $MSDATA/pg_hba.conf
        echo "host all all all md5" >> $MSDATA/pg_hba.conf
    fi

    # if, for some reason, a cold standby is being brought up as a primary
    # remove the standby.signal file
    if [ -f $MSDATA/standby.signal ]; then
        rm $MSDATA/standby.signal
    fi
    # end::configure_primary[]
else
    # tag::configure_standby[]
    echo "Configuring a STANDBY instance..."

    # Set up our password so we can connect to replicate
    # again wont work cause pgpass is only for postgres
    echo "$PRIMARY:5432:replication:repuser:$MYSQL_REPLICA_PASSWORD" >> /var/lib/postgresql/.pgpass

    # Clone the primary database
    rm -rf $PGDATA/*
    pg_basebackup -h $PRIMARY -D $PGDATA -U repuser -v -P -X stream
    chmod -R 700 $PGDATA

    # Add connection info 
    # WONT WORK
    cat << EOF >> $PGDATA/postgresql.conf
        primary_conninfo = 'host=$PRIMARY port=5432 user=repuser password=$MYSQL_REPLICA_PASSWORD'
EOF

    # Notify postgres that this is a standby server
    touch $PGDATA/standby.signal

    # Make sure there is a primary server and failover if there isn't
    monitor &
    # end::configure_standby[]
fi

exec "$@"
