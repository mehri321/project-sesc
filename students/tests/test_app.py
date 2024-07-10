# tests/test_app.py
import unittest
from app import app

class FlaskTestCase(unittest.TestCase):
    
    def setUp(self):
        # Set up a test client
        self.app = app.test_client()
        self.app.testing = True

    def test_home(self):

        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        self.assertIn(b'', response.data)

if __name__ == '__main__':
    unittest.main()
