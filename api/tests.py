from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import User
from django.core.files.uploadedfile import SimpleUploadedFile

class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.force_authenticate(user=self.user)
        self.url = '/api/auth/update_profile/'

    def test_update_profile_text_fields(self):
        data = {
            'first_name': 'New',
            'last_name': 'Name',
            'email': 'newemail@example.com'
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_update_profile_image(self):
        # Create a dummy image
        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        image = SimpleUploadedFile("avatar.gif", image_content, content_type="image/gif")
        
        data = {
            'profile_image': image
        }
        response = self.client.patch(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.profile_image))
