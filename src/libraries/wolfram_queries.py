from pprint import pprint


def ask_wolfram_raw(query, client):
    res = client.query(query)
    pprint(res)
    for pod in res.pods:

        if pod['@id'] == 'Result':
            pprint(pod['subpod'])
            return pod['subpod']['plaintext']
    return "error"
