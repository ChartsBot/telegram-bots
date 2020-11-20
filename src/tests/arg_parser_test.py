import argparse
from pprint import pprint


def analyze_query(query, default_token, default_time_period='d', default_time_start=1, default_options=None):
    preprocessed_query = preprocess_query(query)
    parsed_query = parse_query(preprocessed_query)
    finalized_query = finalize_query(parsed_query[0], parsed_query[1], default_token, default_time_period, default_time_start, default_options)
    return finalized_query


def preprocess_query(query):
    individual_args = query.split(' ')[1:]
    formatted_args = []
    for arg in individual_args:
        if not arg.isnumeric():
            if arg[0] == "-" or arg[0] == "—":  # We already have an option
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

    return token, start_time, time_period, options.replace("-", "")


# --start_time
# --date_type
# --token
def validate_preprocessor():

    to_analyse = [("/c", ""),
                  ("/c 5 d", "--start_time 5 --date_type d"),
                  ("/c abcd", "--token abcd"),
                  ("/chart 5 M abcd", "--start_time 5 --date_type M --token abcd"),
                  ("/chart AE 5 h", "--token AE --start_time 5 --date_type h"),
                  ("/c --fibo", "--fibo"),
                  ("/c --fibo 5 d", "--fibo --start_time 5 --date_type d"),
                  ("/c 5 d --fibo", "--start_time 5 --date_type d --fibo"),
                  ("/c AEIOU 5 d --fibo", "--token AEIOU --start_time 5 --date_type d --fibo"),
                  ("/c AEIOU 5 d --another_type", "--token AEIOU --start_time 5 --date_type d --another_type"),
                  ]

    for query in to_analyse:
        q = query[0]
        analyze_query(q, "rot")
        should_be = query[1]
        q_preprocessed = preprocess_query(q)
        q_is = ' '.join(q_preprocessed).rstrip()
        if q_is != should_be:
            print("NOT GOOD q is : " + q_is + " but should be " + should_be)
        else:
            res = parse_query(q_preprocessed)
            pprint(str(res[0]) + ' - ' + ' '.join(res[1]))
            res = finalize_query(res[0], res[1], "rot")
            pprint(res)


if __name__ == '__main__':
    validate_preprocessor()
    res = analyze_query("/c 5 d —fib")
    pprint(res)
    pprint("done")

# return TOKEN: OPTION, T_START: OPTION, T_TYPE: OPTION, OPTIONS: LIST(STRING)
