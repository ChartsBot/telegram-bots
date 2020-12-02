import os
import json
from pprint import pprint
from web3 import Web3
from cachetools import cached, TTLCache

BASE_PATH = os.environ.get('BASE_PATH')

weth_raw = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2".lower()
weth_checksum = Web3.toChecksumAddress(weth_raw)


def get_decimals_contract(contract):
    decimals = contract.functions.decimals().call()
    return int(decimals)


def get_abi_erc20():
    with open(os.path.abspath(BASE_PATH + "config_files/erc20.abi")) as f:
        abi: str = json.load(f)
    return abi


def __get_pair_tokens(token0, token1, uni_wrapper):
    t0_checksum = Web3.toChecksumAddress(token0)
    t1_checksum = Web3.toChecksumAddress(token1)
    return uni_wrapper.get_pair(t0_checksum, t1_checksum)


@cached(cache=TTLCache(maxsize=1024, ttl=60))
def does_pair_token_eth_exist(token, uni_wrapper):
    res1 = __get_pair_tokens(weth_checksum, token, uni_wrapper)
    if res1 != '0x0000000000000000000000000000000000000000':
        return res1
    else:
        res2 = __get_pair_tokens(token, weth_checksum,uni_wrapper)
        if res2 != '0x0000000000000000000000000000000000000000':
            return res2
        else:
            return None


def get_balance_token_wallet_raw(w3, wallet, token):
    token_checksum = Web3.toChecksumAddress(token)
    wallet_checksum = Web3.toChecksumAddress(wallet)
    contract = w3.eth.contract(address=token_checksum, abi=get_abi_erc20())
    decimals = get_decimals_contract(contract)
    res = contract.functions.balanceOf(wallet_checksum).call() / 10 ** decimals
    return res


def get_lp_value(uni_wrapper, pair_address):
    pair_checksum = Web3.toChecksumAddress(pair_address)
    pair_liq = uni_wrapper.get_pair_liquidity(pair_checksum)
    t0_balance = pair_liq[0]
    t1_balance = pair_liq[1]
    t0_address = uni_wrapper.get_pair_token_address(pair_checksum, 0)
    t1_address = uni_wrapper.get_pair_token_address(pair_checksum, 1)
    amount_lp = int(uni_wrapper.get_amount_lp_total(pair_checksum)) / 10**18
    return [(t0_balance, t0_address), (t1_balance, t1_address), amount_lp]
