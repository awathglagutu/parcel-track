from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_login_failed, user_logged_in, user_logged_out
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    def test_rejects_short_and_common_passwords(self):
        for username, password in (("shortuser", "short1"), ("commonuser", "password")):
            response = self.client.post(reverse("register"), {
                "username": username,
                "email": "test@example.com",
                "password1": password,
                "password2": password,
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(User.objects.filter(username=username).exists())

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="existing", password="StrongPass!456")
        response = self.client.post(reverse("register"), {
            "username": "existing", "email": "", "password1": "StrongPass!456",
            "password2": "StrongPass!456",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="existing").count(), 1)

    def test_markup_is_escaped_and_role_tampering_is_ignored(self):
        response = self.client.post(reverse("register"), {
            "username": "<script>alert(1)</script>", "email": "", "role": "admin",
            "password1": "StrongPass!456", "password2": "StrongPass!456",
        })
        if User.objects.filter(username="<script>alert(1)</script>").exists():
            user = User.objects.get(username="<script>alert(1)</script>")
            self.assertEqual(user.role, User.Role.SELLER)
        else:
            self.assertContains(response, "&lt;script&gt;")
        self.assertNotIn("<script>alert(1)</script>", response.content.decode())


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller", password="StrongPass!456")

    def test_login_errors_are_generic_for_unknown_and_wrong_credentials(self):
        wrong = self.client.post(reverse("login"), {"username": "seller", "password": "wrong"})
        unknown = self.client.post(reverse("login"), {"username": "missing", "password": "wrong"})
        self.assertContains(wrong, "Please enter a correct username and password.")
        self.assertContains(unknown, "Please enter a correct username and password.")

    def test_sql_injection_login_does_not_authenticate(self):
        response = self.client.post(reverse("login"), {
            "username": "' OR 1=1--", "password": "anything",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_session_key_changes_on_login_and_logout_invalidates_session(self):
        self.client.get(reverse("login"))
        before = self.client.session.session_key
        self.client.post(reverse("login"), {"username": "seller", "password": "StrongPass!456"})
        after = self.client.session.session_key
        self.assertNotEqual(before, after)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(reverse("seller_home")).status_code, 302)

    def test_old_session_cookie_is_invalid_after_logout(self):
        self.client.force_login(self.user)
        old_cookie = self.client.cookies["sessionid"].value
        self.client.post(reverse("logout"))
        self.client.cookies["sessionid"] = old_cookie
        self.assertEqual(self.client.get(reverse("seller_home")).status_code, 302)

    def test_logout_rejects_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)


class RoleAccessTests(TestCase):
    def test_seller_and_anonymous_cannot_create_rider(self):
        response = self.client.get(reverse("create_rider"))
        self.assertEqual(response.status_code, 302)
        seller = User.objects.create_user(username="seller", password="StrongPass!456")
        self.client.force_login(seller)
        self.assertEqual(self.client.get(reverse("create_rider")).status_code, 403)

    def test_admin_can_create_rider_and_tampering_does_not_change_role(self):
        admin = User.objects.create_user(username="admin", password="StrongPass!456", role=User.Role.ADMIN)
        self.client.force_login(admin)
        response = self.client.post(reverse("create_rider"), {
            "username": "newrider", "email": "", "role": "admin",
            "password1": "StrongPass!456", "password2": "StrongPass!456",
        })
        self.assertRedirects(response, reverse("admin_home"))
        self.assertEqual(User.objects.get(username="newrider").role, User.Role.RIDER)


class SecurityControlTests(TestCase):
    def test_axes_locks_out_after_five_failures(self):
        User.objects.create_user(username="locked", password="StrongPass!456")
        for _ in range(5):
            self.client.post(reverse("login"), {"username": "locked", "password": "wrong"})
        response = self.client.post(reverse("login"), {
            "username": "locked", "password": "StrongPass!456",
        })
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 200)

    def test_authentication_signal_logs_never_include_password(self):
        user = User.objects.create_user(username="seller", password="StrongPass!456")
        password = "SensitivePass!789"
        with self.assertLogs("security", level="INFO") as captured:
            user_logged_in.send(sender=User, request=None, user=user)
            user_login_failed.send(sender=User, credentials={"username": "seller", "password": password}, request=None)
            user_logged_out.send(sender=User, request=None, user=user)
        combined = "\n".join(captured.output)
        self.assertIn("LOGIN_OK", combined)
        self.assertIn("LOGIN_FAIL", combined)
        self.assertIn("LOGOUT", combined)
        self.assertNotIn(password, combined)
