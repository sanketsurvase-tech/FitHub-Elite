from datetime import timedelta
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import (
    Attendance, GymClass, Member, Membership, NutritionLog, Package, Payment,
    User, WorkoutLog,
)


class GymAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", email="admin@example.com", password="StrongPass123!",
            role=User.Role.ADMIN,
        )
        self.member_user = User.objects.create_user(
            username="member", email="member@example.com", password="StrongPass123!",
        )
        self.member = Member.objects.create(user=self.member_user)
        self.package = Package.objects.create(name="Monthly", duration_days=30, price=49)

    def authenticate(self, user):
        response = self.client.post(
            "/api/auth/token/",
            {"username": user.username, "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_registration_hashes_password_and_creates_member_profile(self):
        response = self.client.post("/api/auth/register/", {
            "username": "new-member",
            "email": "new@example.com",
            "password": "DifferentStrong123!",
            "phone": "555-0101",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-member")
        self.assertTrue(check_password("DifferentStrong123!", user.password))
        self.assertTrue(Member.objects.filter(user=user, phone="555-0101").exists())

    def test_member_cannot_read_other_members(self):
        another_user = User.objects.create_user(
            username="other", email="other@example.com", password="StrongPass123!",
        )
        Member.objects.create(user=another_user)
        self.authenticate(self.member_user)
        response = self.client.get("/api/members/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.member.id)

    def test_member_documents_require_authorized_api_access(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.member.document.save(
                "identity.pdf", SimpleUploadedFile("identity.pdf", b"%PDF-1.4\nprivate"),
            )
            self.authenticate(self.member_user)
            listing = self.client.get("/api/members/")
            document_url = f"/api/members/{self.member.pk}/document/"
            self.assertIn(document_url, listing.data["results"][0]["document_url"])
            download = self.client.get(document_url)
            self.assertEqual(download.status_code, 200)
            self.assertIn("attachment", download["Content-Disposition"])

            other_user = User.objects.create_user(
                username="other", email="other@example.com", password="StrongPass123!",
            )
            Member.objects.create(user=other_user)
            self.client.force_authenticate(user=other_user)
            denied = self.client.get(document_url)
            self.assertEqual(denied.status_code, 404)

    def test_qr_checkin_requires_current_membership_and_toggles_checkout(self):
        self.authenticate(self.admin)
        denied = self.client.post(
            "/api/attendance/check-in/", {"qr_id": str(self.member.qr_id)}, format="json"
        )
        self.assertEqual(denied.status_code, 403)
        today = timezone.localdate()
        Membership.objects.create(
            member=self.member, package=self.package, start_date=today,
            end_date=today + timedelta(days=30),
        )
        checked_in = self.client.post(
            "/api/attendance/check-in/", {"qr_id": str(self.member.qr_id)}, format="json"
        )
        self.assertEqual(checked_in.status_code, 201)
        self.assertEqual(checked_in.data["action"], "check_in")
        checked_out = self.client.post(
            "/api/attendance/check-in/", {"qr_id": str(self.member.qr_id)}, format="json"
        )
        self.assertEqual(checked_out.status_code, 200)
        self.assertEqual(checked_out.data["action"], "check_out")
        self.assertEqual(Attendance.objects.count(), 1)

    def test_admin_only_package_mutations(self):
        self.authenticate(self.member_user)
        response = self.client.post(
            "/api/packages/", {"name": "Annual", "duration_days": 365, "price": "250.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_member_books_for_self_and_capacity_is_enforced(self):
        today = timezone.localdate()
        Membership.objects.create(
            member=self.member, package=self.package, start_date=today,
            end_date=today + timedelta(days=30),
        )
        another_user = User.objects.create_user(
            username="other", email="other@example.com", password="StrongPass123!",
        )
        other_member = Member.objects.create(user=another_user)
        Membership.objects.create(
            member=other_member, package=self.package, start_date=today,
            end_date=today + timedelta(days=30),
        )
        starts = timezone.now() + timedelta(days=1)
        gym_class = GymClass.objects.create(
            name="Capacity test", starts_at=starts,
            ends_at=starts + timedelta(hours=1), capacity=1,
        )
        self.authenticate(self.member_user)
        booked = self.client.post(
            "/api/bookings/", {"gym_class": gym_class.pk}, format="json"
        )
        self.assertEqual(booked.status_code, 201, booked.data)
        self.authenticate(self.admin)
        full = self.client.post(
            "/api/bookings/",
            {"gym_class": gym_class.pk, "member": other_member.pk},
            format="json",
        )
        self.assertEqual(full.status_code, 400)

    def test_exports_support_csv_excel_and_pdf(self):
        self.authenticate(self.admin)
        for output_format, content_type in [
            ("csv", "text/csv"),
            ("excel", "spreadsheetml.sheet"),
            ("pdf", "application/pdf"),
        ]:
            response = self.client.get(f"/api/exports/members/?output={output_format}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(content_type, response["Content-Type"])

    @patch.dict("os.environ", {"MISTRAL_API_KEY": ""})
    def test_ai_endpoint_reports_missing_key_without_fallback(self):
        self.authenticate(self.admin)
        response = self.client.post(
            "/api/ai/advice/", {"prompt": "Suggest a workout"}, format="json"
        )
        self.assertEqual(response.status_code, 503)

    def test_member_workout_and_nutrition_logs_are_private_and_writable(self):
        self.authenticate(self.member_user)
        workout = self.client.post("/api/workout-logs/", {
            "exercise_name": "Goblet squat", "sets": 3, "reps": 10, "weight_kg": "12.5",
        }, format="json")
        self.assertEqual(workout.status_code, 201, workout.data)
        nutrition = self.client.post("/api/nutrition-logs/", {
            "meal_name": "Breakfast", "calories": 450,
            "food_entries": [{"name": "Oats", "grams": 60}],
        }, format="json")
        self.assertEqual(nutrition.status_code, 201, nutrition.data)
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="StrongPass123!",
        )
        other_member = Member.objects.create(user=other_user)
        WorkoutLog.objects.create(
            member=other_member, exercise_name="Deadlift", sets=3, reps=5,
        )
        NutritionLog.objects.create(member=other_member, meal_name="Lunch", calories=650)
        self.assertEqual(self.client.get("/api/workout-logs/").data["count"], 1)
        self.assertEqual(self.client.get("/api/nutrition-logs/").data["count"], 1)

    def test_member_can_download_own_payment_receipt(self):
        payment = Payment.objects.create(member=self.member, amount="49.00", method="card")
        self.authenticate(self.member_user)
        response = self.client.get(f"/api/payments/{payment.pk}/receipt/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_membership_freeze_unfreeze_and_renew_actions(self):
        today = timezone.localdate()
        membership = Membership.objects.create(
            member=self.member, package=self.package, start_date=today,
            end_date=today + timedelta(days=30),
        )
        self.authenticate(self.admin)
        frozen = self.client.post(f"/api/memberships/{membership.pk}/freeze/", {"days": 7}, format="json")
        self.assertEqual(frozen.status_code, 200)
        self.assertEqual(frozen.data["status"], Membership.Status.FROZEN)
        self.assertEqual(frozen.data["end_date"], (today + timedelta(days=37)).isoformat())
        unfrozen = self.client.post(f"/api/memberships/{membership.pk}/unfreeze/", {}, format="json")
        self.assertEqual(unfrozen.status_code, 200)
        renewed = self.client.post(f"/api/memberships/{membership.pk}/renew/", {}, format="json")
        self.assertEqual(renewed.status_code, 201)
        self.assertEqual(renewed.data["member"], self.member.pk)

    def test_member_document_rejects_mismatched_file_content(self):
        self.authenticate(self.admin)
        invalid_document = SimpleUploadedFile("spoofed.pdf", b"not a PDF")
        response = self.client.patch(
            f"/api/members/{self.member.pk}/",
            {"document": invalid_document},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
