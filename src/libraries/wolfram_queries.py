from pprint import pprint


def ask_wolfram_raw(query, client):
    res = client.query(query)
    found_match = None
    try:
        for pod in res.pods:

            if pod['@id'] == 'Result':
                found_match = pod['subpod']['plaintext']
    except KeyError:
        return "error"
    if found_match is None:
        found_match = ""
        for pod in res.pods:
            try:
                found_match += '<b>' + pod['@title'] + '</b>: ' + pod['subpod']['plaintext'] + '\n'
            except TypeError:
                pass
    return found_match if found_match is not None else 'error'
