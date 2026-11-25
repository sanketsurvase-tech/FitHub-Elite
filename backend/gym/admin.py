from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Announcement, Attendance, AuditLog, Booking, Equipment, Exercise, Feedback,
    FitnessProgress, GymClass, MealPlan, Member, Membership, Notification,
    NutritionLog, Package, Payment, Staff, User, WorkoutLog, WorkoutPlan,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Gym access", {"fields": ("role",)}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Gym access", {"fields": ("email", "role")}),)
    list_display = ["username", "email", "first_name", "last_name", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_active"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "joined_at", "active"]
    search_fields = ["user__first_name", "user__last_name", "user__email", "phone"]
    list_filter = ["active", "joined_at"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["member", "package", "start_date", "end_date", "status"]
    list_filter = ["status", "package"]
    search_fields = ["member__user__email", "member__user__last_name"]


admin.site.register([
    Staff, Package, Payment, Attendance, Exercise, WorkoutPlan, MealPlan,
    FitnessProgress, GymClass, Booking, Equipment, Feedback, Announcement,
    WorkoutLog, NutritionLog,
    Notification, AuditLog,
])
