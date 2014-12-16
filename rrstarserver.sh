#!/bin/bash

# This file starts/stops/checks the server

if [ $# -lt 1 ]
then
    echo "Usage: $0 start </path/to/rrstar> [debugflag] [server port]"
    echo "       $0 stop"
    echo "       $0 status"
    exit 2
fi

ACTION=$1


if [ $ACTION == "start" ]
then

    if [ $# -lt 2 ]
    then
        echo "Usage: $0 start </path/to/rrstar> [debugflag] [server port]"
        exit 2
    fi

    BASEPATH=$2

    if [ $# -ge 3 ]
    then
        DEBUGFLAG=$3
    else
        DEBUGFLAG=0
    fi

    if [ $# -ge 4 ]
    then
        SERVERPORT=$4
    else
        SERVERPORT=5005
    fi

    echo "server directory: $BASEPATH"
    echo "server port: $SERVERPORT"
    echo "debug flag: $DEBUGFLAG"

    cd $BASEPATH/src/

    # start the server
    nohup python $BASEPATH/src/rrstarserver.py --log_file_prefix=$BASEPATH/run/logs/rrstarserver.log --debugmode=$DEBUGFLAG --port=$SERVERPORT > $BASEPATH/run/logs/rrstarserver.stdout 2>&1 &

    echo "astroph-coffee server started at:" `date`
    ps -e -o pid,user,vsz,rss,start_time,stat,args | grep -e 'rrstarserver\.py' | grep -v grep | grep -v emacs | grep -v ^vi

elif [ $ACTION == "stop" ]
then

    ps aux | grep -e 'rrstarserver\.py' | grep -v ^vi | grep -v ps | grep -v emacs | awk '{ print $2 }' | xargs kill > /dev/null 2>&1
    echo "server stopped at:" `date`


elif [ $ACTION == "status" ]
then

    echo "Server status: "
    ps -e -o pid,user,vsz,rss,start_time,stat,args | grep -e 'rrstarserver\.py' | grep -v grep | grep -v emacs | grep -v ^vi
    echo

else
    echo "Usage: $0 start </path/to/rrstar> [debugflag] [server port]"
    echo "       $0 stop"
    echo "       $0 status"

fi
