import datetime
import time
import io

import os
import sys

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')

import pandas as pd
import libraries.requests_util as requests_util
import libraries.util as util
from libraries.common_values import chart_dictionary
import numpy as np
import plotly.io as pio
import plotly.express as px
from PIL import Image, ImageDraw, ImageFont, ImageOps

from pprint import pprint

INCREASING_COLOR = '#228B22'
DECREASING_COLOR = '#FF0000'

import matplotlib.pyplot as plt


def __generate_upper_barrier(txt, options=None, width=3200):
    font_size = 40
    unicode_font = ImageFont.truetype("DejaVuSans.ttf", font_size, encoding="unic")

    font = unicode_font
    dark_theme = True
    if options:
        dark_theme = 'white' not in options
    img_color = (255, 255, 255) if not dark_theme else (36, 36, 36)
    txt_color = (0, 0, 0) if not dark_theme else (255, 255, 255)

    bounding_box = [0, 0, width, 100]
    x1, y1, x2, y2 = bounding_box  # For easy reading

    img = Image.new('RGB', (x2, y2), color=img_color)

    d = ImageDraw.Draw(img)

    # Calculate the width and height of the text to be drawn, given font size
    w, h = d.textsize(txt, font=font)

    # Calculate the mid points and offset by the upper left corner of the bounding box
    x = (x2 - x1 - w) / 2 + x1
    y = (y2 - y1 - h) / 2 + y1

    # Write the text to the image, where (x,y) is the top left corner of the text
    d.text((x, y), txt, align='center', font=font, fill=txt_color)

    # d.text((10,10), txt, font=unicode_font, fill=(0,0,0))
    # new_path = path + "trending.png"
    # img.save(new_path)
    return img  # returning raw img


def __calculate_rsi(closes):
    i = 0
    up_prices = []
    down_prices = []
    #  Loop to hold up and down price movements
    while i < len(closes):
        if i == 0:
            up_prices.append(0)
            down_prices.append(0)
        else:
            if (closes[i] - closes[i - 1]) > 0:
                up_prices.append(closes[i] - closes[i - 1])
                down_prices.append(0)
            else:
                down_prices.append(closes[i] - closes[i - 1])
                up_prices.append(0)
        i += 1
    x = 0
    avg_gain = []
    avg_loss = []
    #  Loop to calculate the average gain and loss
    while x < len(up_prices):
        if x < 15:
            avg_gain.append(0)
            avg_loss.append(0)
        else:
            sum_gain = 0
            sum_loss = 0
            y = x - 14
            while y <= x:
                sum_gain += up_prices[y]
                sum_loss += down_prices[y]
                y += 1
            avg_gain.append(sum_gain / 14)
            if sum_loss != 0.0:
                avg_loss.append(abs(sum_loss / 14))
            else:
                avg_loss.append(0.00001)
        x += 1
    p = 0
    rsi = []
    #  Loop to calculate RSI and RS
    while p < len(closes):
        if p < 15:
            rsi.append(np.nan)
        else:
            rs_value = (avg_gain[p] / avg_loss[p])
            rsi.append(100 - (100 / (1 + rs_value)))
        p += 1
    lower_band = np.ones(len(rsi)) * 30
    upper_band = np.ones(len(rsi)) * 70
    return rsi, lower_band.tolist(), upper_band.tolist()


def __moving_average(interval, window_size=10):
    window = np.ones(int(window_size)) / float(window_size)
    return np.convolve(interval, window, 'same')


def __bbands(price, window_size=10, num_of_std=5):
    price_pd = pd.DataFrame(price)
    rolling_mean = price_pd.rolling(window=window_size).mean()
    rolling_std = price_pd.rolling(window=window_size).std()
    upper_band = rolling_mean + (rolling_std * num_of_std)
    lower_band = rolling_mean - (rolling_std * num_of_std)
    return rolling_mean, upper_band, lower_band


def fibonnaci_bands(closes):
    highest = max(closes)
    lowest = min(closes)
    line = dict(color='rgb(169,169,169,0.5)', width=2)
    line_main = dict(color='rgb(0,0,0,1)', width=4)
    top = highest - lowest
    l = []
    percent_23 = top * (1 - 0.236) + lowest
    percent_38 = top * (1 - 0.382) + lowest
    percent_50 = top * (1 - 0.5) + lowest
    percent_62 = top * (1 - 0.618) + lowest
    l.append((pd.DataFrame(np.full(len(closes), lowest)), line_main, "lowest: " + util.pretty_number(lowest)))
    l.append((pd.DataFrame(np.full(len(closes), percent_23)), line, "23%: " + util.pretty_number(percent_23)))
    l.append((pd.DataFrame(np.full(len(closes), percent_38)), line, "38%: " + util.pretty_number(percent_38)))
    l.append((pd.DataFrame(np.full(len(closes), percent_50)), line, "50%: " + util.pretty_number(percent_50)))
    l.append((pd.DataFrame(np.full(len(closes), percent_62)), line, "62%: " + util.pretty_number(percent_62)))
    l.append((pd.DataFrame(np.full(len(closes), top * 1 + lowest)), line_main, "top: " + util.pretty_number(highest)))
    return l


def bollinger_bands(highs, lows, closes, n=20, m=3):
    tp = (pd.DataFrame(highs) + pd.DataFrame(lows) + pd.DataFrame(closes)) / 3
    ma = tp.rolling(n).mean()
    sd = m * tp.rolling(n).std()
    ls_up = dict(color='rgb(255, 0, 0, 0.5)')
    ls_mid = dict(color='rgb(255,20,147, 0.5)')
    ls_low = dict(color='rgb(34,139,34, 0.5)')
    ls_fib = dict(color='rgb(169,169,169,0.5)', width=1)
    l = []
    l.append((ma, ls_mid, True, "Middle Band"))
    l.append((ma + (0.236 * sd), ls_fib, False, "Fib band"))
    l.append((ma + (0.382 * sd), ls_fib, False, "Fib band"))
    l.append((ma + (0.5 * sd), ls_fib, False, "Fib band"))
    l.append((ma + (0.618 * sd), ls_fib, False, "Fib band"))
    l.append((ma + (0.764 * sd), ls_fib, False, "Fib band"))
    l.append((ma + (1 * sd), ls_up, True, "Upper Band"))
    l.append((ma - (0.236 * sd), ls_fib, False, "Fib band"))
    l.append((ma - (0.382 * sd), ls_fib, False, "Fib band"))
    l.append((ma - (0.5 * sd), ls_fib, False, "Fib band"))
    l.append((ma - (0.618 * sd), ls_fib, False, "Fib band"))
    l.append((ma - (0.764 * sd), ls_fib, False, "Fib band"))
    l.append((ma - (1 * sd), ls_low, True, "Lower Band"))
    return l


# Visualisation inspired by https://chart-studio.plotly.com/~jackp/17421/plotly-candlestick-chart-in-python/#/
# Huge thanks to the author!
def __process_and_write_candlelight(dates, openings, closes, highs, lows, volumes, file_path, token_name, options=None):
    data = [dict(
        type='candlestick',
        open=openings,
        high=highs,
        low=lows,
        close=closes,
        x=dates,
        yaxis='y2',
        name='OHLC',
        increasing=dict(line=dict(color=INCREASING_COLOR)),
        decreasing=dict(line=dict(color=DECREASING_COLOR)),
    )]

    # max_price = max(highs)
    # max_y = max_price + max_price * 0.2
    # min_price = min(lows)
    # min_y = max(0, min_price - min_price * 0.2)

    layout = dict()

    fig = dict(data=data, layout=layout)

    fig['layout'] = dict()
    fig['layout']['plot_bgcolor'] = None
    fig['layout']['template'] = 'plotly_dark'
    # fig['layout']['plot_bgcolor'] = 'rgb(250, 250, 250)'
    fig['layout']['autosize'] = False
    fig['layout']['width'] = 1600
    fig['layout']['height'] = 900
    fig['layout']['xaxis'] = dict(rangeslider=dict(visible=False))
    fig['layout']['yaxis'] = dict(domain=[0, 0.19], showticklabels=True, title='Volume ($)', side='right')
    fig['layout']['yaxis2'] = dict(domain=[0.2, 1], title=token_name + ' price ($)', side='right')
    fig['layout']['showlegend'] = False
    fig['layout']['margin'] = dict(t=15, b=15, r=15, l=15)

    if options is not None:
        if "bband" in options:
            ress = bollinger_bands(highs, lows, closes)
            fig['layout']['showlegend'] = True
            for res in ress:
                fig['data'].append(dict(x=dates, y=res[0][0].to_list(), type='scatter', yaxis='y2',
                                        line=res[1], name=res[3],
                                        marker=dict(color='#ccc'), hoverinfo='none',
                                        legendgroup='Bollinger Bands', showlegend=res[2]))

        # cf https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/fibonacci-retracement and https://plotly.com/python/line-charts/
        if "fibo" in options or "fibonnaci" in options or "fib" in options:
            annotations = []
            ress = fibonnaci_bands(closes)
            # fig['layout']['showlegend'] = True
            for res in ress:
                fig['data'].append(dict(x=dates, y=res[0][0].to_list(), type='scatter', yaxis='y2',
                                        line=res[1], name=res[2],
                                        marker=dict(color='#ccc'), hoverinfo='none',
                                        legendgroup='Bollinger Bands', showlegend=False))
                annotations.append(dict(xref='paper', x=0.0, y=res[0][0].to_list()[0],
                                        xanchor='right', yanchor='middle', yref='y2',
                                        text=res[2],
                                        font=dict(family='Arial',
                                                  size=16),
                                        showarrow=False))
            fig['layout']['margin'] = dict(t=15, b=15, r=15, l=100)
            fig['layout']['annotations'] = annotations

        if "rsi" in options or "RSI" in options:
            rsis, lower, upper = __calculate_rsi(closes)
            fig['layout']['yaxis'] = dict(domain=[0, 0.14], title='Volume ($)', side='right')
            fig['layout']['yaxis3'] = dict(domain=[0.15, 0.29], showticklabels=True, title='RSI', side='right')
            fig['layout']['yaxis2'] = dict(domain=[0.3, 1], title=token_name + ' price ($)', side='right')
            fig['data'].append(dict(x=dates, y=rsis, type='scatter', mode='lines',
                                    marker=dict(color='#E377C2'),
                                    yaxis='y3', name='RSI'))
            fig['data'].append(dict(x=dates, y=lower, type='scatter', mode='lines',
                                    marker=dict(color='rgba(13, 55, 13, 0.9)'),
                                    yaxis='y3', name='RSI'))
            fig['data'].append(dict(x=dates, y=upper, type='scatter', mode='lines',
                                    marker=dict(color='rgba(100, 0, 0, 0.9)'),
                                    yaxis='y3', name='RSI'))


        if 'white' in options:
            fig['layout']['template'] = None
            fig['layout']['plot_bgcolor'] = 'rgb(250, 250, 250)'

        if 'avg' in options or 'm' in options or 'average' in options:
            mv_y = __moving_average(closes)
            mv_x = list(dates)

            # Clip the ends
            mv_x = mv_x[5:-5]
            mv_y = mv_y[5:-5]

            fig['data'].append(dict(x=mv_x, y=mv_y, type='scatter', mode='lines',
                                    line=dict(width=2),
                                    marker=dict(color='#E377C2'),
                                    yaxis='y2', name='Moving Average'))

    colors_volume = []

    for i in range(len(closes)):
        if i != 0:
            if closes[i] > closes[i - 1]:
                colors_volume.append(INCREASING_COLOR)
            else:
                colors_volume.append(DECREASING_COLOR)
        else:
            colors_volume.append(DECREASING_COLOR)

    fig['data'].append(dict(x=dates, y=volumes,
                            marker=dict(color=colors_volume),
                            type='bar', yaxis='y', name='Volume'))

    img = pio.to_image(fig=fig, scale=2)
    return io.BytesIO(img)


# t_from and t_to should be numbers, not strings
def __calculate_resolution_from_time(t_from, t_to):
    delta = round(t_to - t_from)
    if delta < 6 * 3600:
        return 1
    elif delta < 13 * 3600:
        return 1
    elif delta < 24 * 3600:
        return 5
    elif delta < 24 * 3600 * 7 + 100:
        return 15
    else:
        return 60


def __preprocess_binance_charts_data(values):
    times = [int(x[0]) for x in values]
    opens = [float(x[1]) for x in values]
    highs = [float(x[2]) for x in values]
    lows = [float(x[3]) for x in values]
    closes = [float(x[4]) for x in values]
    volumes = [float(x[5]) for x in values]

    time_start = datetime.datetime.fromtimestamp(round(times[0] / 1000))
    time_end = datetime.datetime.fromtimestamp(round(times[-1] / 1000))
    time_diff = round((times[1] - times[0]) / (1000 * 60))
    frequency = str(time_diff) + 'min'

    date_list = pd.date_range(start=time_start, end=time_end, freq=frequency).to_pydatetime().tolist()

    return date_list, opens, closes, highs, lows, volumes


def __preprocess_gecko_charts_data(values):
    prices_and_t = values['prices']
    volumes_and_t = values['total_volumes']
    prices = []
    times = []
    volumes = []
    for t in prices_and_t:
        prices.append(t[1])
        times.append(t[0])
    for t in volumes_and_t:
        volumes.append(t[1])

    times_as_datetime = [datetime.datetime.fromtimestamp(round(x / 1000)) for x in times]

    start = times_as_datetime[0]
    end = times_as_datetime[-1]
    start_ts = times[0]
    end_ts = times[1]
    diff = round(end_ts - start_ts)
    if diff < 3600 * 24:  # 0s < x < 1d
        freq = "1min"
    elif diff < 3600 * 24 * 90:  # 1d < x < 90 d -> hourly
        freq = "60min"
    else:
        freq = "1440min"

    closes = prices
    opens = prices
    highs = prices
    lows = prices
    volumes = volumes

    date_list = pd.date_range(start=start, end=end, freq=freq).to_pydatetime().tolist()

    return date_list, opens, closes, highs, lows, volumes


def __preprocess_chartex_data(values, resolution):
    times_from_chartex = [datetime.datetime.fromtimestamp(round(x)) for x in values['t']]

    closes = [float(x) for x in values['c']]
    opens = [float(x) for x in values['o']]
    highs = [float(x) for x in values['h']]
    lows = [float(x) for x in values['l']]
    volumes = [float(x) for x in values['v']]

    frequency = str(resolution) + "min"
    date_list = pd.date_range(start=times_from_chartex[0], end=times_from_chartex[-1],
                              freq=frequency).to_pydatetime().tolist()

    last_index = 0
    missing_dates_count = 0
    for date in date_list:
        if date in times_from_chartex:
            index = times_from_chartex.index(date)
            last_index = index + missing_dates_count
            # check if "too big" value and remove it in this case
            try:
                if index == 0:
                    if highs[0] > highs[1] * 2:
                        # print("reducing highs index 0")
                        highs[0] = min(highs[1] * 3, highs[0] / 2)
                    if lows[0] < lows[1] / 2:
                        # print("increasing lows index 0")
                        lows[0] = max(lows[0] * 2, lows[1] / 2)
                else:
                    # those 2 lines here to fix strange chartex behaviour
                    opens[index] = closes[index - 1]
                    pprint("open: " + str(opens[index]) + " - closes before: " + str(closes[index - 1]))
                    lows[index] = min([opens[index], lows[index], closes[index]])
                    highs[index] = max([opens[index], highs[index], closes[index]])
                    if highs[index] > highs[index - 1] * 2 and highs[index] > highs[index + 1] * 2:
                        # print("reducing highs")
                        highs[index] = (highs[index - 1] + highs[index + 1])
                    if lows[index] < lows[index - 1] / 2 and lows[index] < lows[index + 1] / 2:
                        # print("increasing lows: from " + str(lows[index]) + ' to ' + str(min(lows[index - 1] - lows[index], lows[index + 1] - lows[index])))
                        lows[index] = min(lows[index - 1] - lows[index], lows[index + 1] - lows[index])
            except IndexError:
                pass
        else:
            index = last_index + 1
            price = closes[index - 1]
            closes.insert(index, price)
            highs.insert(index, price)
            lows.insert(index, price)
            opens.insert(index, price)
            volumes.insert(index, 0.0)
            last_index = last_index + 1
            missing_dates_count += 1
    return (date_list, opens, closes, highs, lows, volumes)


def __get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def add_border(img, color):
    return ImageOps.expand(img, border=10, fill=color)


# t_from and t_to should be int epoch second
# return the last price
# options = TA stuff for example
def print_candlestick(token, t_from, t_to, file_path, txt: str = None, options=None):
    resolution = __calculate_resolution_from_time(t_from, t_to)
    check_others = True
    if options is not None:
        if "binance" in options or "b" in options:
            check_others = False
            values = requests_util.get_binance_chart_data(token.upper() + "USDT", t_from, t_to)
            (date_list, opens, closes, highs, lows, volumes) = __preprocess_binance_charts_data(values)
    if check_others:
        if token.upper() in chart_dictionary:
            token_entry = chart_dictionary[token.upper()]
            if token_entry[0] == 'binance':
                values = requests_util.get_binance_chart_data(token_entry[1], t_from, t_to)
                (date_list, opens, closes, highs, lows, volumes) = __preprocess_binance_charts_data(values)
            else:  # defaulting to chartex
                values = requests_util.get_graphex_data(token, resolution, t_from, t_to).json()
                (date_list, opens, closes, highs, lows, volumes) = __preprocess_chartex_data(values, resolution)
        else:
            values = requests_util.get_graphex_data(token, resolution, t_from, t_to).json()
            (date_list, opens, closes, highs, lows, volumes) = __preprocess_chartex_data(values, resolution)
    chart_img_raw = __process_and_write_candlelight(date_list, opens, closes, highs, lows, volumes, file_path, token,
                                                    options)
    chart_img = Image.open(chart_img_raw)
    if txt is not None:
        img_up = __generate_upper_barrier(txt, options)
        chart_img = __get_concat_v(img_up, chart_img)
    border_color = '#013220' if closes[-1] > closes[0] else '#3f0000'
    img_final = add_border(chart_img, color=border_color)
    img_final.save(file_path)
    return closes[-1]


def get_piechart(tokens_owned, path: str, percent_thresehold=0.03):
    total_value = 0
    for token in tokens_owned:
        total_value += token.get_amount_usd_token(0.0)
    values_usd = [(x.ticker, x.get_amount_usd_token(0.0)) for x in tokens_owned if x.get_percent(total_value) > percent_thresehold]
    values_raw = [x[1] for x in values_usd]
    values_name = [x[0] for x in values_usd]

    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    missing_amount = total_value - sum(values_raw)
    values_raw += [missing_amount]
    values_name += ['Others']
    d = {'amount_usd': values_raw, 'label': values_name}
    df = pd.DataFrame(data=d)
    fig = px.pie(df, values='amount_usd', names='label',
                 color_discrete_sequence=px.colors.sequential.Agsunset)  # https://plotly.com/python/builtin-colorscales/
    fig.update_traces(texttemplate="%{label}<br>%{percent}<br>%{value:$.2f}")
    fig.update_layout(uniformtext_minsize=16, uniformtext_mode='hide')
    fig.update_layout(width=1000, height=1000)
    pio.write_image(fig=fig, file=path, scale=1)


def test_print_candlestick(token, t_from, t_to, resolution=1):
    t_1 = time.time_ns() // 1000000
    values = requests_util.get_graphex_data(token, resolution, t_from, t_to).json()
    t_2 = time.time_ns() // 1000000
    (date_list, opens, closes, highs, lows, volumes) = __preprocess_chartex_data(values, resolution)
    print("0 = " + str(date_list[0]))
    print("last = " + str(date_list[-1]))
    print("size = " + str(len(date_list)))
    time_between = date_list[-1] - date_list[0]
    print("diff: " + str(time_between))

    # __process_and_write_candlelight(date_list, opens, closes, highs, lows, volumes, file_path, token)
    print("time chartex query = " + str(t_2 - t_1))


def main():
    token = "bbra"
    t_to = int(time.time())
    t_from = int(time.time()) - 3600 * 24
    # print_candlestick(token, t_from, t_to, "testaaa2.png", "coucou", ["bband"])
    print_candlestick(token, t_from, t_to, "testaaa2.png", "coucou", ["dark", "rsi"])


if __name__ == '__main__':
    main()
