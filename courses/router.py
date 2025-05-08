from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from auth import AuthInstructor

from django.db.models import Count
from . import models, schemas, api


router = Router(auth=AuthInstructor())
api = api.API()


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


@router.get("/{int:courseID}", response=schemas.CourseSchemaFull, auth=None)
def get_course(request, courseID: int):
    qs = models.Course.objects.prefetch_related('lesson_set')
    obj = get_object_or_404(qs, pk=courseID)
    status, data = api.get_user(obj.instructor_id)
    if status == 200:
        obj.instructor = data
    return obj


@router.put("/{int:courseID}", response=schemas.CourseSchema)
def update_course(request, courseID: int, body: schemas.CourseSchemaIn):
    qs = models.Course.objects.filter(
        instructor_id=request.auth['id']).annotate(lesson_count=Count('lesson'))
    obj = get_object_or_404(qs, pk=courseID)
    data = body.dict(exclude_unset=True)

    for attr, value in data.items():
        setattr(obj, attr, value)
    obj.save()
    return obj


@router.delete("/{int:courseID}", response={204: None})
def delete_course(request, courseID: int):
    qs = models.Course.objects.filter(instructor_id=request.auth['id'])
    obj = get_object_or_404(qs, pk=courseID)
    obj.delete()
    return 204, None
