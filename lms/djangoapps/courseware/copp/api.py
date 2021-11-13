import requests

BASE_URL = "http://web:8000/api/v1"
REFRESH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYzNjEzNjg0MywianRpIjoiYzFjMjBmMGNkNjQ5NGY1ZmE2YTY4NzMxNjI5NGNkNDciLCJ1c2VyX2lkIjoiMzcyYjE5M2YtYWQ2NC00MGE2LTgwYjItNmRkMmE3MWNkMjRmIn0.j7vHt1EM5cjsif6h9dS8J7ebZ1zdGlmfGUmbq0xBH7k"

class Api():

    def get(self, url, params=None):
        token = self._getRefreshToken()
        headers = {'Authorization': "Bearer {}".format(token)}
        response = requests.get(f"{BASE_URL}/{url}", params=params, headers=headers)
        return response.json()

    def _getRefreshToken(self):
        data = {"refresh" : REFRESH_TOKEN}
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/token/refresh/", headers=headers, json=data)
        response.raise_for_status()
        token = response.json()   
        return token['access']