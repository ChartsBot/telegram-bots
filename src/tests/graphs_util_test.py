import src.libraries.graphs_util as graphs
import src.libraries.requests_util as requests_util

if __name__ == '__main__':
    values = requests_util.get_graphex_data(token, resolution, t_from, t_to).json()
    (date_list, opens, closes, highs, lows, volumes) = __preprocess_chartex_data(values, resolution)

