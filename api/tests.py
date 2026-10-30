from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Couple, Memory
from django.core.files.uploadedfile import SimpleUploadedFile

class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!'
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/auth/update_profile/'

    def test_update_profile_text_fields(self):
        data = {
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'phone_number': '1234567890'
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirst')
        self.assertEqual(self.user.last_name, 'NewLast')
        self.assertEqual(self.user.phone_number, '1234567890')

    def test_email_change_requires_verification_security(self):
        """Security: Direct email change without OTP verification must be rejected"""
        data = {
            'email': 'hacker@example.com'
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('code'), 'EMAIL_CHANGE_REQUIRED')

    def test_update_profile_image(self):
        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        image = SimpleUploadedFile("avatar.gif", image_content, content_type="image/gif")
        
        data = {
            'profile_image': image
        }
        response = self.client.patch(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.profile_image))


class AuthAndRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user_success(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_duplicate_email_registration_rejected(self):
        User.objects.create_user(username='existing', email='duplicate@example.com', password='Password123!')
        data = {
            'username': 'differentuser',
            'email': 'duplicate@example.com',
            'password': 'Password123!'
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_blocked(self):
        """Security: Protected API endpoints must block unauthenticated access"""
        response = self.client.get('/api/couple/my_couple/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CoupleIsolationSecurityTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='u1@example.com', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', email='u2@example.com', password='Password123!')
        self.other_user = User.objects.create_user(username='other', email='other@example.com', password='Password123!')

        # Couple 1
        self.couple1 = Couple.objects.create(partner_1=self.user1, partner_2=self.user2)
        # Other couple
        self.couple2 = Couple.objects.create(partner_1=self.other_user)

        # Create memory in couple 1
        self.memory1 = Memory.objects.create(
            couple=self.couple1,
            title='Secret Memory Couple 1',
            description='Our private story',
            date='2026-01-01'
        )

        self.client = APIClient()

    def test_idor_protection_between_couples(self):
        """Security: Other user must NOT be able to view, edit, or delete Memory from Couple 1"""
        self.client.force_authenticate(user=self.other_user)

        # Attempt to retrieve Couple 1's memory
        response = self.client.get(f'/api/memories/{self.memory1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to list memories - should not contain Couple 1's memory
        list_response = self.client.get('/api/memories/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        memory_ids = [m['id'] for m in list_response.data]
        self.assertNotIn(self.memory1.id, memory_ids)

        # Attempt to delete Couple 1's memory
        delete_response = self.client.delete(f'/api/memories/{self.memory1.id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Memory.objects.filter(id=self.memory1.id).exists())
