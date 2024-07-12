import unittest
from app import create_app, db
from app.models import User, Organization

class AuthTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register_user_success(self):
        response = self.client.post('/auth/register', json={
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "password": "password",
            "phone": "1234567890"
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['status'], 'success')
        self.assertIn('accessToken', data['data'])

    def test_login_user_success(self):
        self.client.post('/auth/register', json={
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "password": "password",
            "phone": "1234567890"
        })
        response = self.client.post('/auth/login', json={
            "email": "john@example.com",
            "password": "password"
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertIn('accessToken', data['data'])

    def test_registration_validation_errors(self):
        response = self.client.post('/auth/register', json={
            "firstName": "",
            "lastName": "",
            "email": "",
            "password": "",
            "phone": ""
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(data['errors']), 4)

    def test_duplicate_email_or_userid(self):
        self.client.post('/auth/register', json={
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "password": "password",
            "phone": "1234567890"
        })
        response = self.client.post('/auth/register', json={
            "firstName": "Jane",
            "lastName": "Doe",
            "email": "john@example.com",
            "password": "password",
            "phone": "0987654321"
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(data['errors']), 1)

if __name__ == "__main__":
    unittest.main()
