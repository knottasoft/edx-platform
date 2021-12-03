import requests
from django.conf import settings

BASE_URL = settings.COPP_API_URL
REFRESH_TOKEN = settings.COPP_API_REFRESH_TOKEN

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