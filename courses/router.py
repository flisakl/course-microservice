from django.shortcuts import get_object_or_404
from ninja import Router

from auth import AuthBearer, decode_jwt

from . import models, schemas


router = Router()


