from ninja import Schema, ModelSchema, Field

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
        fields = ['id', 'name']


class InstructorSchema(Schema):
    id: int
    username: str


class CourseSchemaFull(ModelSchema):
    instructor: InstructorSchema | None = None
    lessons: list[LessonSchema] = Field([], alias='lesson_set')

    class Meta:
        model = models.Course
        fields = ['id', 'name', 'description']
