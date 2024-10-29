import os

import requests
from requests.auth import HTTPBasicAuth

class ApiRequests:
    @staticmethod
    def post(parameters: dict = None) -> requests:
        print(parameters)
        response = requests.post(
            os.getenv("OPENPROJECT_URL"),
            auth=HTTPBasicAuth(os.getenv("OPENPROJECT_LOGIN"), os.getenv("OPENPROJECT_API_KEY")),
            json=parameters,
        )
        print(response.text)
        return response
