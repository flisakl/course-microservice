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


class InstructorSchema(Schema):
    id: int
    username: str


class CourseSchemaFull(ModelSchema):
    instructor: InstructorSchema | None = None
    lessons: list[LessonSchema] = Field([], alias='lesson_set')

    class Meta:
        model = models.Course
        fields = ['id', 'name', 'description']
