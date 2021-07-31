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
test_mode = True

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

# ~~~~~============== FUNCTIONS ==============~~~~~

def fully_collect(prices):
    c = True
    c = c and (prices["BOND"][0]!= 0)
    c = c and (prices["BOND"][1]!= 0)
    c = c and (prices["VALBZ"][0]!= 0)
    c = c and (prices["VALBZ"][1]!= 0)
    c = c and (prices["VALE"][0]!= 0)
    c = c and (prices["VALE"][1]!= 0)
    c = c and (prices["GS"][0]!= 0)
    c = c and (prices["GS"][1]!= 0)
    c = c and (prices["MS"][0]!= 0)
    c = c and (prices["MS"][1]!= 0)
    c = c and (prices["WFC"][0]!= 0)
    c = c and (prices["WFC"][1]!= 0)
    c = c and (prices["XLF"][0]!= 0)
    c = c and (prices["XLF"][1]!= 0)
    return c

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
    prices = {"BOND":[0, 0], "VALBZ":[0, 0], "VALE":[0, 0], "GS":[0, 0], "MS":[0, 0], "WFC":[0, 0], "XLF":[0, 0]} # buy, sell
    while True:
        print(prices)
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
            try:
                prices[message["symbol"]][0] = message["buy"][0][0]
            except:
                print("empty buy 77")
            try:
                prices[message["symbol"]][1] = message["sell"][0][0]
            except:
                print("empty sell 81")
        if fully_collect(prices):
            # VALBZ & VALE
            fair_value = (prices["VALBZ"][0]+prices["VALBZ"][1])/2
            vb = prices['VALE'][1] + 1
            vs = prices['VALE'][0] - 1
            if fair_value != 0:
                if vb < fair_value:
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "VALE", "dir": "BUY", "price": vb, "size": 1})
                    order_id += 1
                    read_from_exchange(exchange)
                if vs > fair_value:
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "VALE", "dir": "SELL", "price": vs, "size": 1})
                    order_id += 1
                    read_from_exchange(exchange)

            r = (order_id * 19751 % 5813 ) % 10
            print(r)
            if r < 7:
            # ETF
                fair_gs = (prices["GS"][0] + prices["GS"][1])/2
                fair_ms = (prices["MS"][0] + prices["MS"][1])/2
                fair_wfc = (prices["WFC"][0] + prices["WFC"][1])/2
                fair_etf = 0.1 * (3 * 1000 + 2*fair_gs + 3*fair_ms+ 2*fair_wfc)

                if fair_etf != 0:
                    xb = prices["XLF"][1] + 1
                    xs = prices["XLF"][0] - 1
                    if xb< fair_etf:
                        write_to_exchange(exchange,{"type":"add","order_id":order_id,"symbol": "XLF", "dir": "BUY", "price": xb, "size": 1})
                        order_id +=1
                        read_from_exchange(exchange)
                    if xs> fair_etf:
                        write_to_exchange(exchange,{"type":"add","order_id":order_id,"symbol": "XLF", "dir": "SELL", "price": xs, "size": 1})
                        order_id +=1
                        read_from_exchange(exchange)

            else:
            # ETF convert
                if 10*prices["XLF"][0]>3*prices["BOND"][1]+2*prices["GS"][1]+3*prices["MS"][1]+2*prices["WFC"][1]+100:
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "BOND", "dir": "BUY", "price": prices["BOND"][1]-1, "size": 3})
                    order_id += 1
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "GS", "dir": "BUY", "price": prices["GS"][1]-1, "size": 2})
                    order_id += 1
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "MS", "dir": "BUY", "price": prices["MS"][1]-1, "size": 3})
                    order_id += 1
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "WFC", "dir": "BUY", "price": prices["WFC"][1]-1, "size": 2})
                    order_id += 1

                    #convert
                    write_to_exchange(exchange,{"type": "convert", "order_id": order_id, "symbol": "XLF", "dir": "BUY", "size": 10})
                    order_id+=1
                    #sell
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "XLF", "dir": "SELL", "price": prices["XLF"][0]+1, "size": 10})
                elif 10*prices["XLF"][1]+100>3*prices["BOND"][0]+2*prices["GS"][0]+3*prices["MS"][0]+2*prices["WFC"][0]:
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "XLF", "dir": "BUY", "price": prices["XLF"][1]-1, "size": 10})
                    order_id += 1
                    #convert
                    write_to_exchange(exchange,{"type": "convert", "order_id": order_id, "symbol": "XLF", "dir": "SELL", "size": 10})
                    order_id+=1
                    #sell
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "BOND", "dir": "SELL", "price": prices["BOND"][0]+1, "size": 3})
                    order_id += 1
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "GS", "dir": "SELL", "price": prices["GS"][0]+1, "size": 2})
                    order_id += 1
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "MS", "dir": "SELL", "price": prices["MS"][0]+1, "size": 3})
                    order_id += 1
                    write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "WFC", "dir": "SELL", "price": prices["WFC"][0]+1, "size": 2})
                    order_id += 1

            # BOND
            write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "BOND", "dir": "BUY", "price": 999, "size": 5})
            order_id += 1
            read_from_exchange(exchange)
            write_to_exchange(exchange, {"type":"add","order_id":order_id,"symbol": "BOND", "dir": "SELL", "price": 1001, "size": 5})
            order_id += 1
            read_from_exchange(exchange)

if __name__ == "__main__":
    main()
