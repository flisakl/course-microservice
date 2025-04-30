from django.test import TestCase
from ninja.testing import TestClient

from courses.router import router
from courses.api import login_or_register
from courses.models import Course, Lesson
from auth import decode_jwt

client = TestClient(router)


USER_TOKEN = login_or_register('testuser', 'testpassword')[1]['token']
INSTRUCTOR_TOKEN = login_or_register(
    'testinstructor', 'testpassword', True
)[1]['token']

USER_ID = decode_jwt(USER_TOKEN)['id']
INSTRUCTOR_ID = decode_jwt(INSTRUCTOR_TOKEN)['id']


class UserAPITests(TestCase):
    def auth_header(self, token: str):
        return {
            'Authorization': f'Bearer {token}'
        }

    def test_instructor_can_create_course(self):
        data = {
            "name": "My new course",
            "description": "Description of my awesome course"
        }

        response = client.post(
            "",
            json=data,
            headers=self.auth_header(INSTRUCTOR_TOKEN)
        )
        json = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json['name'], data['name'])
        self.assertEqual(json['description'], data['description'])
        self.assertEqual(json['instructor_id'], INSTRUCTOR_ID)

    def test_reqular_user_can_not_create_course(self):
        response = client.post(
            "",
            json={},
            headers=self.auth_header(USER_TOKEN)
        )

        self.assertEqual(response.status_code, 401)

    def test_reqular_user_can_access_course_list(self):
        courses = Course.objects.bulk_create([
            Course(name='First course', description='Test', instructor_id=INSTRUCTOR_ID),
            Course(name='Second course', description='Test', instructor_id=INSTRUCTOR_ID),
        ])
        Lesson.objects.create(name='First lesson', content='Bla bla bla', course=courses[0])

        response = client.get("")
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['count'], 2)
        self.assertEqual(json['items'][0]['name'], 'First course')
        self.assertEqual(json['items'][0]['lesson_count'], 1)
