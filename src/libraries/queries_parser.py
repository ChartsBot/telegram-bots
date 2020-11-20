import argparse


def analyze_query(query, default_token, default_time_period='d', default_time_start=1, default_options=None):
    preprocessed_query = preprocess_query(query)
    parsed_query = parse_query(preprocessed_query)
    token, start_time, time_period, options = finalize_query(parsed_query[0], parsed_query[1], default_token, default_time_period, default_time_start, default_options)
    return token, start_time, time_period, options


def preprocess_query(query):
    individual_args = query.split(' ')[1:]
    formatted_args = []
    for arg in individual_args:
        if not arg.isnumeric():
            if arg[0] == "-":  # We already have an option
                formatted_args.append(arg)
            elif len(arg) == 1:  # Type of date, like m, d, h, ...
                formatted_args.append("--date_type")
                formatted_args.append(arg)
            else:  # it's the token
                formatted_args.append("--token")
                formatted_args.append(arg)

        else:
            start_time = abs(int(arg))
            formatted_args.append("--start_time")
            formatted_args.append(str(start_time))
    return formatted_args


def parse_query(query):
    parser = argparse.ArgumentParser()
    parser.add_argument("--token")
    parser.add_argument("--date_type")
    parser.add_argument("--start_time", type=int)

    args, unknown = parser.parse_known_args(query)

    return args, unknown


def finalize_query(args, unknown_args, default_token, default_time_period='d', default_time_start=1, default_options=None):

    token = args.token if args.token else default_token
    start_time = args.start_time if args.start_time else default_time_start
    time_period = args.date_type if args.date_type else default_time_period
    options = unknown_args if unknown_args is not [] else default_options

    return token, start_time, time_period, options
