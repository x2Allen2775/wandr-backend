import requests

try:
    res = requests.post('http://127.0.0.1:8000/api/auth/forgot-password', data={'email': 'maheshsingh2775@gmail.com'})
    print("STATUS:", res.status_code)
except Exception as e:
    print(e)
