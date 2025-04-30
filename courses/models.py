from django.db import models
from django.core.validators import MinValueValidator


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    instructor_id = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return self.name


class Access(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user_id = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "course_id", "user_id", name="course_user_unique"
            )
        ]


class Lesson(models.Model):
    name = models.CharField("Title", max_length=200)
    content = models.TextField()
    number = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    video = models.FileField('lesson-videos/', null=True, blank=True)

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    quiz_id = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)], null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['number']
