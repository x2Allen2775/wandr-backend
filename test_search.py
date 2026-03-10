import requests
import json

try:
    # Need a token
    # Let's just login to get one
    login_res = requests.post('http://127.0.0.1:8000/api/auth/login', data={'username': 'allen2775', 'password': 'password'})
    token = login_res.json().get('access_token')
    
    # Now test the search
    res = requests.get('http://127.0.0.1:8000/api/profile/search?q=hardik', headers={'Authorization': f'Bearer {token}'})
    print("STATUS:", res.status_code)
    print("content:", json.dumps(res.json(), indent=2))
except Exception as e:
    print(e)
