from pprint import pprint


def ask_wolfram_raw(query, client):
    res = client.query(query)
    found_match = None
    try:
        for pod in res.pods:

            pprint(pod)
            if pod['@id'] == 'Result':
                pprint(pod['subpod'])
                found_match = pod['subpod']['plaintext']
    except KeyError:
        return "error"
    if found_match is None:
        found_match = ""
        for pod in res.pods:
            found_match += pod['subpod']['plaintext'] + ' - '
    return found_match if found_match is not None else 'error'
