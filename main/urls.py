from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from jwt.exceptions import ExpiredSignatureError
from courses.router import router

api = NinjaAPI()
api.add_router('/', router)


@api.exception_handler(ExpiredSignatureError)
def on_expired_token(request, exc):
    return api.create_response(
        request,
        {"detail": "Token has expired"},
        status=401
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api.urls)
]
