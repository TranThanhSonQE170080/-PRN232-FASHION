import json
import sys
from urllib import request, error

url = 'https://prn232-fashion.onrender.com/api/v1/auth/login'
data = json.dumps({'email': 'admin@gmail.com', 'password': 'Password123!'}).encode('utf-8')
req = request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode('utf-8')
        print('STATUS:', resp.getcode())
        print('BODY:', body)
except error.HTTPError as e:
    try:
        body = e.read().decode('utf-8')
    except Exception:
        body = '<no body>'
    print('HTTP_ERROR:', e.code)
    print('BODY:', body)
    sys.exit(1)
except Exception as e:
    print('ERROR:', str(e))
    sys.exit(2)
