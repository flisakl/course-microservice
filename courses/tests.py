from django.test import TestCase
from ninja.testing import TestClient

from courses.router import router
from courses.api import API
from courses.models import Course, Lesson, Access
from auth import decode_jwt

client = TestClient(router)
api = API()


USER_TOKEN = api.login_or_register('testuser', 'testpassword')[1]['token']
INSTRUCTOR_TOKEN = api.login_or_register(
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
            Course(name='First course', description='Test',
                   instructor_id=INSTRUCTOR_ID),
            Course(name='Second course', description='Test',
                   instructor_id=INSTRUCTOR_ID),
        ])
        Lesson.objects.create(name='First lesson',
                              content='Bla bla bla', course=courses[0])

        response = client.get("")
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['count'], 2)
        self.assertIn(
            json['items'][0]['name'],
            ['First course', 'Second course']
        )

    def test_guest_can_access_course_details(self):
        course = Course.objects.create(
            name='Microservices 101',
            description='Test',
            instructor_id=INSTRUCTOR_ID
        )
        lessons = Lesson.objects.bulk_create([
            Lesson(
                name='What are API Gateways', content='Bla bla bla', number=3,
                course=course
            ),
            Lesson(
                name='How to create microservice', content='Bla', number=1,
                course=course
            ),
            Lesson(
                name='How to talk to other services', content='Bla ', number=2,
                course=course
            )
        ])

        response = client.get(f"/{course.pk}")
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['name'], course.name)
        self.assertEqual(len(json['lessons']), 3)
        self.assertEqual(json['lessons'][0]['name'], lessons[1].name)
        self.assertEqual(json['lessons'][1]['name'], lessons[2].name)

    def test_instructor_can_edit_his_course(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        data = {'name': 'Good name', 'description': 'Good description'}
        url = f"/{course.pk}"

        response = client.put(
            url, json=data, headers=self.auth_header(INSTRUCTOR_TOKEN))
        response2 = client.put(
            url, json=data, headers=self.auth_header(USER_TOKEN))
        json = response.json()

        self.assertEqual(response2.status_code, 401)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['name'], data['name'])
        self.assertEqual(json['description'], data['description'])

    def test_instructor_can_delete_his_course(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        url = f"/{course.pk}"

        response = client.delete(
            url, headers=self.auth_header(INSTRUCTOR_TOKEN))
        response2 = client.delete(url, headers=self.auth_header(USER_TOKEN))

        self.assertEqual(response2.status_code, 401)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Course.objects.filter(pk=course.pk).exists())

    def test_instructor_can_add_lesson_to_his_course(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        url = f"/{course.pk}/lessons"
        data = {
            "name": "First Lesson",
            "content": "Today we're gonna talk about...",
            "number": 1,
        }
        h = self.auth_header(INSTRUCTOR_TOKEN)

        response = client.post(url, data=data, headers=h)
        json = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json['name'], data['name'])
        self.assertEqual(json['content'], data['content'])
        self.assertEqual(json['number'], data['number'])

    def test_user_can_access_course_lesson(self):
        course = Course.objects.create(
            name='Has access', description='Bad description', instructor_id=INSTRUCTOR_ID)
        course2 = Course.objects.create(
            name='No access', description='Bad description', instructor_id=INSTRUCTOR_ID)
        l = Lesson.objects.create(
            name='First lesson', content='test', course=course)
        l2 = Lesson.objects.create(
            name='Another lesson in different course', content='test', course=course2)
        url = f"/{course.pk}/lessons/{l.pk}"
        url2 = f"/{course2.pk}/lessons/{l2.pk}"
        Access.objects.create(user_id=USER_ID, course=course)

        h = self.auth_header(USER_TOKEN)

        response = client.get(url, headers=h)
        response2 = client.get(url2, headers=h)
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 404)
        self.assertEqual(json['name'], 'First lesson')
