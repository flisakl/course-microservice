from django.db import models
from django.core.validators import MinValueValidator
import string
import random


CODE_LENGTH = 10


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    instructor_id = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)]
    )
    code = models.CharField(max_length=CODE_LENGTH, unique=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self):
        chars = string.ascii_uppercase + string.digits
        instructor_len = len(str(self.instructor_id))
        if instructor_len == CODE_LENGTH:
            raise ValueError(
                "Too many users in the system. Increase course access maximum length")
        while True:
            code = ''.join(random.choices(
                chars,
                k=CODE_LENGTH - instructor_len
            ))
            code = f"{self.instructor_id}{code}"
            if not Course.objects.filter(code=code).exists():
                return code


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


class JoinRequest(models.Model):
    user_id = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)]
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
