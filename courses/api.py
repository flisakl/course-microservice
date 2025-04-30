import requests


class API:
    URLS = {
        'users': 'http://kong:8000/users'
    }

    def headers(self, token: str):
        return {
            'Authorization': f'Bearer {token}'
        }

    def get_user(self, user_id: int):
        response = requests.get(
            f'{self.URLS["users"]}/{user_id}',
        )
        return response.status_code, response.json()

    def create_user(
            self,
            username: str,
            password: str,
            is_instructor: bool = False
    ):
        response = requests.post(
            f'{self.URLS["users"]}/register',
            json={'username': username, 'password': password,
                  'is_instructor': is_instructor
                  }
        )
        return response.status_code, response.json()

    def login(self, username: str, password: str):
        response = requests.post(
            f'{self.URLS["users"]}/login',
            json={'username': username, 'password': password}
        )
        return response.status_code, response.json()

    def login_or_register(
        self,
        username: str,
        password: str,
        instructor: bool = False
    ):
        status, response = self.login(username, password)
        if status != 200:
            return self.create_user(username, password, instructor)
        return status, response
