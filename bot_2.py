#!/usr/bin/python
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import time

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name = "YYDS"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = False

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index = 0
prod_exchange_hostname = "production"

port = 25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile("rw", 1)


def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    return json.loads(exchange.readline())


# ~~~~~============== MAIN LOOP ==============~~~~~


def main():
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    order_id = 1
    fair_value = 0
    while True:
        message = read_from_exchange(exchange)
        if message["type"] == "close":
            print("The round has ended")
            break
        if message["type"] == "hello":
            pass
        if message["type"] == "ack":
            pass
        if message["type"] == "reject":
            print(message)
            pass
        if message["type"] == "book":
            if message["symbol"] == "VALBZ":
                try:
                    fair_value = (message["buy"][0][0]+message["sell"][0][0])/2
                except:
                    print("ERROR 78", message)
            elif message["symbol"] == "VALE":
                try:
                    vb = message["sell"][0][0] + 1
                    vs = message["buy"][0][0] - 1
                    if fair_value != 0:
                        if vb < fair_value:
                            write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "VALE", "dir": "BUY", "price": vb, "size": 1})
                            order_id += 1
                            message=read_from_exchange(exchange)
                        if vs > fair_value:
                            write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "VALE", "dir": "SELL", "price": vs, "size": 1})
                            order_id += 1
                            message=read_from_exchange(exchange)
                except:
                    print("ERROR 93", message)

        # start place
        write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "BOND", "dir": "BUY", "price": 999, "size": 5})
        order_id += 1
        message=read_from_exchange(exchange)
        write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "BOND", "dir": "SELL", "price": 1001, "size": 5})
        order_id += 1
        message=read_from_exchange(exchange)

if __name__ == "__main__":
    main()
