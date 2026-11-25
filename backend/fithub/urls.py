from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from gym.views import (
    AIAdviceView, AnnouncementViewSet, AttendanceCheckInView, AttendanceViewSet,
    AuditLogViewSet, BookingViewSet, DashboardView, EquipmentViewSet, ExerciseViewSet,
    ExportView, FeedbackViewSet, FitnessProgressViewSet, GymClassViewSet,
    MealPlanViewSet, MemberViewSet, MembershipViewSet, NotificationViewSet,
    NutritionLogViewSet, PackageViewSet, PaymentViewSet, RegistrationView,
    StaffViewSet, WorkoutLogViewSet, WorkoutPlanViewSet, ProfileView, api_health,
)

router = DefaultRouter()
router.register("members", MemberViewSet)
router.register("staff", StaffViewSet)
router.register("packages", PackageViewSet)
router.register("memberships", MembershipViewSet)
router.register("payments", PaymentViewSet)
router.register("attendance", AttendanceViewSet)
router.register("exercises", ExerciseViewSet)
router.register("workouts", WorkoutPlanViewSet)
router.register("workout-logs", WorkoutLogViewSet)
router.register("meals", MealPlanViewSet)
router.register("nutrition-logs", NutritionLogViewSet)
router.register("progress", FitnessProgressViewSet)
router.register("classes", GymClassViewSet)
router.register("bookings", BookingViewSet)
router.register("equipment", EquipmentViewSet)
router.register("feedback", FeedbackViewSet)
router.register("announcements", AnnouncementViewSet)
router.register("notifications", NotificationViewSet)
router.register("audit-logs", AuditLogViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", api_health),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/register/", RegistrationView.as_view(), name="register"),
    path("api/auth/me/", ProfileView.as_view(), name="profile"),
    path("api/dashboard/", DashboardView.as_view(), name="dashboard"),
    path("api/attendance/check-in/", AttendanceCheckInView.as_view(), name="check-in"),
    path("api/ai/advice/", AIAdviceView.as_view(), name="ai-advice"),
    path("api/exports/<str:resource>/", ExportView.as_view(), name="export"),
    path("api/", include(router.urls)),
]
