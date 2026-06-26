import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse


class PageViewTests(TestCase):
    pages = {
        "monitoring:home": "ChildGuard AI",
        "monitoring:dashboard": "Guardian Dashboard",
        "monitoring:profile": "Child Profile",
        "monitoring:resources": "Safety Resources",
        "monitoring:assistant": "Digital safety and web assistant",
        "monitoring:about": "About ChildGuard AI",
    }

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="parent",
            password="secure-test-password",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_landing_and_login_are_public(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("monitoring:landing")).status_code, 200)
        self.assertEqual(self.client.get(reverse("monitoring:login")).status_code, 200)

    def test_dashboard_redirects_anonymous_users_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("monitoring:dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('monitoring:login')}?next={reverse('monitoring:dashboard')}",
        )

    def test_valid_login_opens_existing_app_home(self):
        self.client.logout()
        response = self.client.post(
            reverse("monitoring:login"),
            {"username": "parent", "password": "secure-test-password"},
        )
        self.assertRedirects(response, reverse("monitoring:home"))

    def test_pages_render_successfully(self):
        for route_name, expected_text in self.pages.items():
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_text)


class AssistantViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="parent",
            password="secure-test-password",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def post_chat(self, message, history=None):
        return self.client.post(
            reverse("monitoring:assistant"),
            data=json.dumps({"message": message, "history": history or []}),
            content_type="application/json",
        )

    def test_empty_prompt_is_rejected(self):
        response = self.post_chat("  ")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Please enter a message.")

    @override_settings(GROQ_API_KEY="")
    def test_missing_api_key_uses_offline_safety_mode(self):
        response = self.post_chat("How should we manage screen time?")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "offline")
        self.assertIn("screen-time plan", response.json()["reply"])

    @override_settings(GROQ_API_KEY="test-key", GROQ_MODEL="groq/compound")
    @patch("monitoring.views.request_groq_reply")
    def test_valid_prompt_uses_groq_with_history(self, groq_reply):
        groq_reply.return_value = {
            "reply": "Review privacy settings together.",
            "web_used": True,
        }
        response = self.post_chat(
            "What else should we review?",
            [{"role": "user", "content": "How can I improve family privacy?"},
             {"role": "assistant", "content": "Start with app permissions."}],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "Review privacy settings together.")
        self.assertTrue(response.json()["web_used"])
        history = groq_reply.call_args.args[1]
        self.assertEqual(history[-1]["content"], "Start with app permissions.")

    @override_settings(GROQ_API_KEY="test-key")
    def test_long_prompt_is_rejected_before_api_call(self):
        response = self.post_chat("a" * 2001)

        self.assertEqual(response.status_code, 400)
        self.assertIn("under 2000 characters", response.json()["error"])


class RegistrationViewTests(TestCase):
    def test_registration_page_renders(self):
        response = self.client.get(reverse("monitoring:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "e-KYC Enrollment")

    def test_registration_under_18_rejected(self):
        data = {
            "username": "newguardian",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "fullname": "John Doe",
            "aadhaar_verified": "true",
            "aadhaar_name": "John Doe",
            "aadhaar_number": "123456789012",
            "aadhaar_mobile": "9876543210",
            "aadhaar_dob": "01/01/2015",
            "aadhaar_age": "11",
            "aadhaar_address": "123 Street Name, City, State",
        }
        response = self.client.post(reverse("monitoring:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You must be at least 18 years old")

    def test_registration_name_mismatch_rejected(self):
        data = {
            "username": "newguardian",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "fullname": "John Doe",
            "aadhaar_verified": "true",
            "aadhaar_name": "Jane Doe",
            "aadhaar_number": "123456789012",
            "aadhaar_mobile": "9876543210",
            "aadhaar_dob": "01/01/1990",
            "aadhaar_age": "36",
            "aadhaar_address": "123 Street Name, City, State",
        }
        response = self.client.post(reverse("monitoring:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not match Aadhaar profile name")

    def test_registration_missing_aadhaar_fields_rejected(self):
        data = {
            "username": "newguardian",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "fullname": "John Doe",
            "aadhaar_verified": "true",
            "aadhaar_name": "John Doe",
            # missing aadhaar_number
            "aadhaar_mobile": "9876543210",
            "aadhaar_dob": "01/01/1990",
            "aadhaar_age": "36",
            "aadhaar_address": "123 Street Name, City, State",
        }
        response = self.client.post(reverse("monitoring:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A valid 12-digit Aadhaar number is required")

    def test_registration_success(self):
        data = {
            "username": "newguardian",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "fullname": "John Doe",
            "aadhaar_verified": "true",
            "aadhaar_name": "John Doe",
            "aadhaar_number": "123456789012",
            "aadhaar_mobile": "9876543210",
            "aadhaar_dob": "01/01/1990",
            "aadhaar_age": "36",
            "aadhaar_address": "123 Street Name, City, State",
        }
        response = self.client.post(reverse("monitoring:register"), data)
        self.assertRedirects(response, reverse("monitoring:home"))
        self.assertTrue(get_user_model().objects.filter(username="newguardian").exists())
