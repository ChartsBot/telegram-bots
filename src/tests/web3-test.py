import datetime
import os
from web3 import Web3
import time
from pprint import pprint

infura_url = os.environ.get('INFURA_URL')
web3 = Web3(Web3.HTTPProvider(infura_url))

def ts_from_block_num(block_num):
    block = web3.eth.getBlock(block_num)
    block_time = block.timestamp
    return block_time


def estimate_block_height_by_timestamp(timestamp):
    block_found = False
    last_block_number = web3.eth.blockNumber
    close_in_seconds = 600

    block_time = timestamp
    a = last_block_number
    b = int(last_block_number / 2)
    f_a = ts_from_block_num(a)
    f_b = ts_from_block_num(b)
    diff = int((f_a - f_b))
    while diff > close_in_seconds:
        if f_b > timestamp:
            pprint("f_b > timestamp")
            a = b
            b = int(b / 2)
            f_a = ts_from_block_num(a)
            f_b = ts_from_block_num(b)
            diff = abs(int((f_a - f_b)))
            pprint(diff)
        else:
            pprint("f_b < timestamp")
            c = int((a + b) / 2)
            a = b
            b = c
            f_a = ts_from_block_num(a)
            f_b = ts_from_block_num(b)
            diff = abs(int((f_a - f_b)))
            pprint(diff)
    pprint("done for target " + str(timestamp))
    pprint("a = " + str(a) + " - ts = " + str(ts_from_block_num(a)))
    pprint("b = " + str(b) + " - ts = " + str(ts_from_block_num(b)))
    return ""


if __name__ == '__main__':
    block_now = estimate_block_height_by_timestamp(round(time.time()))
    block_yesterday = estimate_block_height_by_timestamp(round(time.time()) - 3600 * 24)
    block_7days_ago = estimate_block_height_by_timestamp(round(time.time()) - 3600 * 24 * 7)

    print(block_now)
    print(block_yesterday)
    print(block_7days_ago)

