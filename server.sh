#!/bin/bash
name=students
host=127.0.0.1
port=8001
maxchildren=10
maxspare=8
minspare=5
maxrequests=100

case $1 in
	start)
	/CTF/students/www/manage.py runfcgi method=prefork maxchildren=$maxchildren maxspare=$maxspare minspare=$minspare maxrequests=$maxrequests host=$host port=$port pidfile=/tmp/$name.pid
	;;
	stop)
	kill -9 `cat /tmp/$name.pid`
	;;
	restart|reload)
		$0 stop
		sleep 1
		$0 start
	;;
	*) echo "Usage ./server.sh {start|stop|restart}";;
esac

exit 0
