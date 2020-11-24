def ask_wolfram_raw(query, client):
    res = client.query(query)
    for pod in res.pods:

        if pod['@id'] == 'Result':
            return pod['subpod']['plaintext']
