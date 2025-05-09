from ninja import Schema, ModelSchema, Field
from pydantic import ValidationError, field_validator

from . import models


class CourseSchemaIn(Schema):
    name: str
    description: str | None = None


class CourseSchema(ModelSchema):
    lesson_count: int = 0

    class Meta:
        model = models.Course
        fields = ['id', 'name', 'description', 'instructor_id']


class CourseSchemaWithCode(CourseSchema):
    code: str


class LessonSchema(ModelSchema):
    course_id: int = 0

    class Meta:
        model = models.Lesson
        fields = ['id', 'name', 'number']


class LessonSchemaIn(Schema):
    name: str
    content: str
    number: int
    quiz_id: int | None = None

    @field_validator('quiz_id', mode='after')
    @classmethod
    def is_positive(cls, value: int | None) -> int | None:
        if value:
            if value < 0:
                raise ValidationError('Must be bigger than 0')
        return value


class LessonSchemaFull(LessonSchema):
    content: str
    video: str | None
    quiz_id: int | None


class UserSchema(Schema):
    id: int
    username: str


class CourseSchemaFull(ModelSchema):
    instructor: dict | None = None
    lessons: list[LessonSchema] = Field([], alias='lesson_set')

    class Meta:
        model = models.Course
        fields = ['id', 'name', 'description']


class CodeSchema(Schema):
    code: str


class RequestSchema(Schema):
    id: int
    course: CourseSchema
    user: dict


class RequestAnswer(Schema):
    id: int
    accept: bool = False


class RequestAnswerSchema(Schema):
    requests: list[RequestAnswer] = []
