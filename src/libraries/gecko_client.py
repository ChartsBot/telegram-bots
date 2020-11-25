import requests
from cachetools import cached, TTLCache
from pprint import pprint


url_price_full = "https://api.coingecko.com/api/v3/simple/price?ids=$ID&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"

url_price_old = "https://api.coingecko.com/api/v3/coins/$ID/market_chart?vs_currency=usd&days=$DAYS&interval=daily"


@cached(cache=TTLCache(maxsize=1024, ttl=30))
def get_price_now_full(ticker):
    updated_url = url_price_full.replace("$ID", ticker)
    res = requests.get(updated_url).json()[ticker]
    pprint(res)
    price_usd = res['usd']
    change_percentage = res['usd_24h_change']
    volume_24_usd = res['usd_24h_vol']
    mcap_usd = res['usd_market_cap']
    return price_usd, change_percentage, volume_24_usd, mcap_usd


@cached(cache=TTLCache(maxsize=1024, ttl=600))
def get_price_at(ticker: str, days: int):
    updated_url = url_price_old\
        .replace("$ID", ticker)\
        .replace("$DAYS", str(days))
    res = requests.get(updated_url).json()['prices'][0][1]
    return res


if __name__ == '__main__':
    pass
    from pprint import pprint
    name = 'bitcoin'
    price_usd, change_percentage, volume_24_usd, mcap_usd = get_price_now_full(name)
    pprint(price_usd)
    pprint(change_percentage)
    pprint(volume_24_usd)
    pprint(mcap_usd)
    res2 = get_price_at(name, 7)
    pprint(res2)
    res2 = get_price_at(name, 6)
    pprint(res2)
    res2 = get_price_at(name, 5)
    pprint(res2)
    res2 = get_price_at(name, 1)
    pprint(res2)
    res2 = get_price_at(name, 7)
    pprint(res2)
    res2 = get_price_at(name, 6)
    pprint(res2)
    res2 = get_price_at(name, 5)
    pprint(res2)
    res2 = get_price_at(name, 1)
    pprint(res2)


