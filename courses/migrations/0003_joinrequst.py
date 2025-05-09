# Generated by Django 5.2 on 2025-05-09 15:20

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_course_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='JoinRequst',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.PositiveBigIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course')),
            ],
        ),
    ]
