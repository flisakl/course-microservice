from ninja.security import HttpBearer
from ninja.errors import AuthenticationError
from django.conf import settings
import jwt


def decode_jwt(token: str, check_expiration: bool = True) -> dict:
    return jwt.decode(
        token, settings.RSA_PUBLIC_KEY, algorithms=["RS256"],
        options={
            'verify_exp': check_expiration,
        }
    )


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token:
            try:
                decoded = decode_jwt(token)
                return decoded
            except jwt.exceptions.ExpiredSignatureError:
                raise AuthenticationError(401, "Token has expired")
            except jwt.exceptions.DecodeError:
                raise AuthenticationError(401, "Invalid token")


class AuthInstructor(AuthBearer):
    def authenticate(self, request, token):
        decoded = super().authenticate(request, token)
        if decoded and decoded['is_instructor']:
            return decoded
