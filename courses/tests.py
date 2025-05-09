from django.test import TestCase
from ninja.testing import TestClient

from courses.router import router
from courses.api import API
from courses.models import Course, Lesson, Access, JoinRequest
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

    def test_instructor_can_edit_lesson_from_his_course(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        course2 = Course.objects.create(
            name='Another course', description='Bad description', instructor_id=INSTRUCTOR_ID + 1)
        l = Lesson.objects.create(
            name='First lesson', content='test', course=course)
        l2 = Lesson.objects.create(
            name='Another lesson in different course', content='test', course=course2)
        url = f"/{course.pk}/lessons/{l.pk}"
        url2 = f"/{course2.pk}/lessons/{l2.pk}"
        data = {
            "name": "Corrected lesson name",
            "content": "Fixed lesson content",
            "number": 10,
        }
        h = self.auth_header(INSTRUCTOR_TOKEN)

        response = client.put(url, data=data, headers=h)
        response2 = client.put(url2, data=data, headers=h)
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 404)
        self.assertEqual(json['name'], data['name'])
        self.assertEqual(json['content'], data['content'])
        self.assertEqual(json['number'], data['number'])

    def test_instructor_can_delete_lesson_from_his_course(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        course2 = Course.objects.create(
            name='Another course', description='Bad description', instructor_id=INSTRUCTOR_ID + 1)
        l = Lesson.objects.create(
            name='First lesson', content='test', course=course)
        l2 = Lesson.objects.create(
            name='Another lesson in different course', content='test', course=course2)
        url = f"/{course.pk}/lessons/{l.pk}"
        url2 = f"/{course2.pk}/lessons/{l2.pk}"
        h = self.auth_header(INSTRUCTOR_TOKEN)

        response = client.delete(url, headers=h)
        response2 = client.delete(url2, headers=h)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Lesson.objects.filter(pk=l.pk).exists())
        self.assertEqual(response2.status_code, 404)
        self.assertTrue(Lesson.objects.filter(pk=l2.pk).exists())

    def test_user_can_join_the_course_with_valid_code(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        data = {"code": course.code}
        data2 = {"code": "junk"}
        url = "/join"
        h = self.auth_header(USER_TOKEN)

        response = client.post(url, json=data, headers=h)
        response2 = client.post(url, json=data2, headers=h)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 404)

    def test_user_can_send_join_request(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        url = f"/{course.pk}/requests"
        h = self.auth_header(USER_TOKEN)

        response = client.post(url, headers=h)
        response2 = client.post(url, headers=h)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response2.status_code, 200)

    def test_instructor_can_access_join_request_for_his_course(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        course2 = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID+1)
        url = f"/{course.pk}/requests"
        url2 = f"/{course2.pk}/requests"
        JoinRequest.objects.bulk_create(
            [
                JoinRequest(course=course, user_id=USER_ID),
                JoinRequest(course=course, user_id=USER_ID + 1),
                JoinRequest(course=course2, user_id=USER_ID),
            ]
        )
        h = self.auth_header(INSTRUCTOR_TOKEN)

        response = client.get(url, headers=h)
        response2 = client.get(url2, headers=h)
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response2.status_code, 404)
        self.assertEqual(len(json), 2)

    def test_instructor_can_accept_join_requests_for_his_course(self):
        course = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID)
        course2 = Course.objects.create(
            name='Bad name', description='Bad description', instructor_id=INSTRUCTOR_ID+1)
        requests = JoinRequest.objects.bulk_create(
            [
                JoinRequest(course=course, user_id=USER_ID),
                JoinRequest(course=course, user_id=USER_ID + 1),
                JoinRequest(course=course2, user_id=USER_ID + 1),
                JoinRequest(course=course2, user_id=USER_ID),
            ]
        )
        data = {
            "requests": [
                {"id": requests[0].pk, "accept": True},
                {"id": requests[1].pk, "accept": False},
                {"id": requests[2].pk, "accept": True},
                {"id": requests[3].pk, "accept": False},
            ]
        }
        url = f"/{course.pk}/requests/answer"
        url2 = f"/{course2.pk}/requests/answer"
        h = self.auth_header(INSTRUCTOR_TOKEN)

        response = client.post(url, json=data, headers=h)
        response2 = client.post(url2, json=data, headers=h)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response2.status_code, 404)
        self.assertEqual(
            len(JoinRequest.objects.filter(course_id=course.pk)), 0)
        self.assertEqual(
            len(Access.objects.filter(course_id=course.pk)), 1)
        self.assertEqual(
            len(JoinRequest.objects.filter(course_id=course2.pk)), 2)
