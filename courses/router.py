from django.shortcuts import get_object_or_404
from ninja import Router, File, Form, Body
from ninja.pagination import paginate
from ninja.files import UploadedFile

from auth import AuthInstructor, AuthBearer

from django.db.models import Count
from . import models, schemas, api


router = Router(auth=AuthInstructor())
api = api.API()


@router.post("/", response={201: schemas.CourseSchemaWithCode})
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


@router.post("/join", response={200: dict}, auth=AuthBearer())
def join_course(request, data: schemas.CodeSchema):
    obj = get_object_or_404(models.Course, code=data.code)
    obj, created = models.Access.objects.get_or_create(
        course=obj, user_id=request.auth['id'])
    if not created:
        return 200, {'detail': "You've already joined the course"}
    else:
        return 200, {'detail': "Success"}


@router.post("/{int:courseID}/lessons", response={201: schemas.LessonSchemaFull})
def create_lesson(request, courseID: int, data: Form[schemas.LessonSchemaIn], video: UploadedFile | None = File(None)):
    data = data.dict()
    data['course_id'] = courseID
    get_object_or_404(models.Course, pk=courseID)

    if video:
        data['video'] = video

    obj = models.Lesson(**data)
    obj.save()
    return 201, obj


@router.get("/{int:courseID}/lessons", response=list[schemas.LessonSchema], auth=None)
def get_course_lessons(request, courseID: int):
    objs = models.Lesson.objects.filter(course_id=courseID).order_by('number')
    return objs


@router.get("/{int:courseID}/lessons/{int:lessonID}", response=schemas.LessonSchemaFull, auth=AuthBearer())
def get_course_lesson(request, courseID: int, lessonID: int):
    get_object_or_404(models.Access, course_id=courseID,
                      user_id=request.auth['id'])
    obj = get_object_or_404(models.Lesson, pk=lessonID)
    return obj


@router.put("/{int:courseID}/lessons/{int:lessonID}", response=schemas.LessonSchemaFull)
def update_lesson(request, courseID: int, lessonID: int, data: Form[schemas.LessonSchemaIn], video: UploadedFile | None = File(None)):
    data = data.dict()
    data['course_id'] = courseID
    get_object_or_404(models.Course, pk=courseID,
                      instructor_id=request.auth['id'])

    obj = get_object_or_404(models.Lesson, pk=lessonID)

    for key, value in data.items():
        setattr(obj, key, value)

    if video:
        obj.video.save(video.name, video, save=False)
    obj.save()
    return obj


@router.delete("/{int:courseID}/lessons/{int:lessonID}", response={204: None})
def delete_lesson(request, courseID: int, lessonID: int):
    get_object_or_404(models.Course, pk=courseID,
                      instructor_id=request.auth['id'])
    obj = get_object_or_404(models.Lesson, pk=lessonID)
    obj.delete()
    return 204, None


@router.get("/{int:courseID}/requests", response=list[schemas.RequestSchema], auth=AuthInstructor())
def get_join_requests(request, courseID: int):
    get_object_or_404(models.Course, pk=courseID,
                      instructor_id=request.auth['id'])
    requests = models.JoinRequest.objects.filter(course_id=courseID)

    user_ids = [x.user_id for x in requests]
    code, users = api.get_users(user_ids)
    for r in requests:
        for u in users:
            if r.user_id == u['id']:
                r.user = u

    return requests


@router.post("/{int:courseID}/requests", response={200: dict, 201: dict}, auth=AuthBearer())
def send_join_request(request, courseID: int):
    obj = get_object_or_404(models.Course, pk=courseID)
    obj, created = models.JoinRequest.objects.get_or_create(course=obj, user_id=request.auth['id'])

    if not created:
        return 200, {'detail': "You've already send the request, wait for response."}
    else:
        return 201, {'detail': "Response has been sent"}


@router.post("/{int:courseID}/requests/answer", response={204: None})
def answer_course_join_requests(request, courseID: int, data: schemas.RequestAnswerSchema):
    course = get_object_or_404(models.Course, pk=courseID, instructor_id=request.auth['id'])
    requests = models.JoinRequest.objects.filter(pk__in=[x.id for x in data.requests], course_id=course.pk)
    new_access_objs = []

    for obj in requests:
        for rd in data.requests:
            if obj.pk == rd.id and rd.accept is True:
                new_access_objs.append(models.Access(user_id=obj.user_id, course=course))

    requests.delete()
    models.Access.objects.bulk_create(new_access_objs)

    return 204, None
