from pprint import pprint


def ask_wolfram_raw(query, client):
    res = client.query(query)
    for pod in res.pods:

        pprint(pod)
        if pod['@id'] == 'Result':
            pprint(pod['subpod'])
            return pod['subpod']['plaintext']
    return "error"
