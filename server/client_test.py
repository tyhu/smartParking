import requests

#URL = 'http://128.237.136.19:9001'
#URL = 'http://128.2.208.89:9001'
URL = 'http://localhost:9001'

#r = requests.get(URL)
#print r
#print r.headers
#print r.text

#payload = {'cmd': 'request_slot'}
#payload = {'cmd': 'unlock', 'camid':'6', 'slotid':'225,596,745,960'}
#payload = {'cmd':'img','camid':'6'}
#files = {'imgfile':open('6.jpg','rb')}
payload = {'cmd':'request_img','camid':'6'}


#r = requests.post(URL, data=payload, files = files)
r = requests.post(URL, data=payload)
print r
print r.headers
#print r.text
with open('test.jpg', 'wb') as f:
    for chunk in r:
        f.write(chunk)
