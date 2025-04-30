from ninja import Schema, ModelSchema

from . import models


class CourseSchemaIn(Schema):
    name: str
    description: str | None = None


class CourseSchema(ModelSchema):
    lesson_count: int = 0

    class Meta:
        model = models.Course
        fields = ['id', 'name', 'description', 'instructor_id']
