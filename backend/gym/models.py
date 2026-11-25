import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .validators import validate_member_document


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        TRAINER = "trainer", "Trainer"
        RECEPTIONIST = "receptionist", "Receptionist"
        MEMBER = "member", "Member"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="member_profile")
    phone = models.CharField(max_length=32, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    joined_at = models.DateField(default=timezone.localdate)
    photo = models.ImageField(upload_to="members/photos/", blank=True, validators=[
        FileExtensionValidator(["jpg", "jpeg", "png", "webp"])
    ])
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=32, blank=True)
    document = models.FileField(upload_to="members/documents/", blank=True, validators=[validate_member_document])
    qr_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user)


class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    title = models.CharField(max_length=100)
    phone = models.CharField(max_length=32, blank=True)
    specialties = models.CharField(max_length=240, blank=True)
    schedule = models.JSONField(default=dict, blank=True)
    hired_at = models.DateField(default=timezone.localdate)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.title}"


class Package(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    duration_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FROZEN = "frozen", "Frozen"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="memberships")
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name="memberships")
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    frozen_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member} - {self.package}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        BANK = "bank", "Bank transfer"
        ONLINE = "online", "Online"

    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="payments")
    membership = models.ForeignKey(Membership, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    method = models.CharField(max_length=10, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member} - {self.amount}"


class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="attendance")
    checked_in_at = models.DateTimeField(default=timezone.now)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=16, default="manual")
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.member} - {self.checked_in_at:%Y-%m-%d %H:%M}"


class Exercise(models.Model):
    name = models.CharField(max_length=120, unique=True)
    muscle_group = models.CharField(max_length=80)
    equipment = models.CharField(max_length=120, blank=True)
    instructions = models.TextField(blank=True)

    def __str__(self):
        return self.name


class WorkoutPlan(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="workouts")
    trainer = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="workouts")
    name = models.CharField(max_length=120)
    details = models.JSONField(default=list, blank=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.member}"


class WorkoutLog(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="workout_logs")
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs")
    exercise_name = models.CharField(max_length=120)
    performed_at = models.DateField(default=timezone.localdate)
    sets = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    reps = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    weight_kg = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member} - {self.exercise_name} - {self.performed_at}"


class MealPlan(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="meal_plans")
    trainer = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="meal_plans")
    name = models.CharField(max_length=120)
    meals = models.JSONField(default=list, blank=True)
    daily_calories = models.PositiveIntegerField(default=0)
    protein_g = models.PositiveIntegerField(default=0)
    carbs_g = models.PositiveIntegerField(default=0)
    fats_g = models.PositiveIntegerField(default=0)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.member}"


class NutritionLog(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="nutrition_logs")
    meal_name = models.CharField(max_length=120)
    food_entries = models.JSONField(default=list, blank=True)
    calories = models.PositiveIntegerField(default=0)
    protein_g = models.PositiveIntegerField(default=0)
    carbs_g = models.PositiveIntegerField(default=0)
    fats_g = models.PositiveIntegerField(default=0)
    logged_at = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member} - {self.meal_name} - {self.logged_at}"


class FitnessProgress(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="progress")
    recorded_at = models.DateField(default=timezone.localdate)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    body_fat_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    measurements = models.JSONField(default=dict, blank=True)
    goal = models.CharField(max_length=240, blank=True)
    photo = models.ImageField(upload_to="members/progress/", blank=True, validators=[
        FileExtensionValidator(["jpg", "jpeg", "png", "webp"])
    ])

    def __str__(self):
        return f"{self.member} - {self.recorded_at}"


class GymClass(models.Model):
    name = models.CharField(max_length=120)
    trainer = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="classes")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=12, validators=[MinValueValidator(1)])
    location = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.starts_at:%Y-%m-%d %H:%M}"


class Booking(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        CANCELLED = "cancelled", "Cancelled"
        ATTENDED = "attended", "Attended"

    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name="bookings")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="bookings")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.BOOKED)
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["gym_class", "member"], name="unique_member_class_booking")]


class Equipment(models.Model):
    class Status(models.TextChoices):
        OPERATIONAL = "operational", "Operational"
        MAINTENANCE = "maintenance", "Maintenance"
        RETIRED = "retired", "Retired"

    name = models.CharField(max_length=120)
    inventory_code = models.CharField(max_length=64, unique=True)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPERATIONAL)
    last_maintenance = models.DateField(null=True, blank=True)
    maintenance_due = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.inventory_code})"


class Feedback(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)


class Announcement(models.Model):
    title = models.CharField(max_length=160)
    message = models.TextField()
    audience = models.CharField(max_length=16, choices=User.Role.choices, blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=160)
    message = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
