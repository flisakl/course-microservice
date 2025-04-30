from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from auth import AuthInstructor

from django.db.models import Count
from . import models, schemas


router = Router(auth=AuthInstructor())


@router.post("/", response={201: schemas.CourseSchema})
def create_course(request, data: schemas.CourseSchemaIn):
    data = data.dict()
    data['instructor_id'] = request.auth['id']
    course = models.Course.objects.create(**data)
    return 201, course


@router.get("/", response=list[schemas.CourseSchema], auth=None)
@paginate
def list_courses(request):
    return models.Course.objects.annotate(lesson_count=Count('lesson')).all()
