import unittest
import json
from app import app  # Import your main app

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # Create a test client
        self.app = app.test_client()
        self.app.testing = True

        # Sample user data for testing
        self.sample_user = {
    "first_name": "John",
    "last_name": "Doe",
    "username": "johnbhaiji",
    "email": "johndoess@example.com",
    "country_code": "+1",
    "mobile_number": "1234567890",
    "company_name": "ExampleCorp",
    "city": "Example City",
    "state": "Example State",
    "country": "Example Country",
    "medicare_bot_usage": "yes",
    "package": "premium",
    "password": "securepassword1234444"
}


    def test_register_user(self):
        # Test user registration
        response = self.app.post('/register', data=json.dumps(self.sample_user), content_type='application/json')
        
        # Debugging output
        print("Register Status Code:", response.status_code)
        print("Register Response Data:", response.data)
        
        # Check that the user was successfully registered
        self.assertEqual(response.status_code, 200)
        self.assertIn("User registered successfully", response.json.get("message", ""))

    def test_login_user(self):
        # First, register the user to ensure they exist
        self.app.post('/register', data=json.dumps(self.sample_user), content_type='application/json')

        # Test user login
        login_data = {
            "username": self.sample_user["username"],
            "password": self.sample_user["password"]
        }
        response = self.app.post('/login', data=json.dumps(login_data), content_type='application/json')
        
        # Debugging output
        print("Login Status Code:", response.status_code)
        print("Login Response Data:", response.data)
        
        # Check for successful login
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json)
        self.token = response.json["token"]  # Save the token for later use

    def test_access_dashboard(self):
        # First, register and log in the user to get a token
        self.app.post('/register', data=json.dumps(self.sample_user), content_type='application/json')
        login_data = {
            "username": self.sample_user["username"],
            "password": self.sample_user["password"]
        }
        login_response = self.app.post('/login', data=json.dumps(login_data), content_type='application/json')
        self.token = login_response.json.get("token")

        # Test access to the protected dashboard
        response = self.app.get('/dashboard', headers={"Authorization": f"Bearer {self.token}"})
        
        # Debugging output
        print("Dashboard Access Status Code:", response.status_code)
        print("Dashboard Access Response Data:", response.data)
        
        # Check for successful access
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome to your dashboard", response.json.get("message", ""))

if __name__ == '__main__':
    unittest.main()
