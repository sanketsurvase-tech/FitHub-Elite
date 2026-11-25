from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Announcement, Attendance, AuditLog, Booking, Equipment, Exercise, Feedback, FitnessProgress,
    GymClass, MealPlan, Member, Membership, Notification, Package, Payment,
    NutritionLog, Staff, User, WorkoutLog, WorkoutPlan,
)


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]


class MemberSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    photo_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.filter(role=User.Role.MEMBER), write_only=True, required=False
    )

    class Meta:
        model = Member
        fields = [
            "id", "user", "user_id", "phone", "date_of_birth", "joined_at", "photo",
            "photo_url", "emergency_contact_name", "emergency_contact_phone", "document",
            "document_url", "qr_id",
            "active", "created_at",
        ]
        read_only_fields = ["qr_id", "created_at"]
        extra_kwargs = {
            "photo": {"write_only": True},
            "document": {"write_only": True},
        }

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        path = f"/api/members/{obj.pk}/photo/"
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path

    def get_document_url(self, obj):
        if not obj.document:
            return None
        path = f"/api/members/{obj.pk}/document/"
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path


class StaffSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.filter(role__in=[User.Role.TRAINER, User.Role.RECEPTIONIST]),
        write_only=True,
    )

    class Meta:
        model = Staff
        fields = ["id", "user", "user_id", "title", "phone", "specialties", "schedule", "hired_at", "active"]


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"


class MembershipSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)

    class Meta:
        model = Membership
        fields = "__all__"

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["paid_at"]

    def validate(self, attrs):
        member = attrs.get("member", getattr(self.instance, "member", None))
        membership = attrs.get("membership", getattr(self.instance, "membership", None))
        if membership and member and membership.member_id != member.pk:
            raise serializers.ValidationError({"membership": "Choose a membership belonging to this member."})
        return attrs


class AttendanceSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = "__all__"
        read_only_fields = ["recorded_by", "checked_in_at"]


class WorkoutPlanSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)

    class Meta:
        model = WorkoutPlan
        fields = "__all__"


class WorkoutLogSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all(), required=False)

    class Meta:
        model = WorkoutLog
        fields = "__all__"

    def validate(self, attrs):
        request_user = self.context["request"].user
        member = attrs.get("member")
        if member is None and self.instance:
            member = self.instance.member
        if member is None:
            member = getattr(request_user, "member_profile", None)
        if member is None and request_user.role != User.Role.MEMBER:
            raise serializers.ValidationError({"member": "This field is required."})
        plan = attrs.get("plan", getattr(self.instance, "plan", None))
        if plan and member and plan.member_id != member.pk:
            raise serializers.ValidationError({"plan": "Choose a workout plan belonging to this member."})
        return attrs


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = "__all__"


class MealPlanSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)

    class Meta:
        model = MealPlan
        fields = "__all__"


class NutritionLogSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)

    class Meta:
        model = NutritionLog
        fields = "__all__"


class FitnessProgressSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)
    bmi = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = FitnessProgress
        fields = "__all__"
        extra_kwargs = {"photo": {"write_only": True}}

    def get_bmi(self, obj):
        if not obj.weight_kg or not obj.height_cm:
            return None
        height_m = float(obj.height_cm) / 100
        return round(float(obj.weight_kg) / (height_m * height_m), 1)

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        path = f"/api/progress/{obj.pk}/photo/"
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path


class GymClassSerializer(serializers.ModelSerializer):
    trainer_name = serializers.SerializerMethodField()
    booked_count = serializers.SerializerMethodField()

    class Meta:
        model = GymClass
        fields = "__all__"

    def get_booked_count(self, obj):
        if hasattr(obj, "_booked_count"):
            return obj._booked_count
        return obj.bookings.filter(status="booked").count()

    def get_trainer_name(self, obj):
        return obj.trainer.user.get_full_name() if obj.trainer else None

    def validate(self, attrs):
        starts = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts and ends and ends <= starts:
            raise serializers.ValidationError({"ends_at": "Class end time must be after its start time."})
        trainer = attrs.get("trainer", getattr(self.instance, "trainer", None))
        capacity = attrs.get("capacity", getattr(self.instance, "capacity", None))
        if self.instance and capacity is not None and self.instance.bookings.filter(
            status=Booking.Status.BOOKED
        ).count() > capacity:
            raise serializers.ValidationError({"capacity": "Capacity cannot be lower than the current bookings."})
        if trainer and starts and ends:
            conflicts = GymClass.objects.filter(
                trainer=trainer, starts_at__lt=ends, ends_at__gt=starts
            )
            if self.instance:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            if conflicts.exists():
                raise serializers.ValidationError({"trainer": "This trainer already has a class during that time."})
        return attrs

    def update(self, instance, validated_data):
        with transaction.atomic():
            GymClass.objects.select_for_update().get(pk=instance.pk)
            capacity = validated_data.get("capacity", instance.capacity)
            if instance.bookings.filter(status=Booking.Status.BOOKED).count() > capacity:
                raise serializers.ValidationError({"capacity": "Capacity cannot be lower than the current bookings."})
            return super().update(instance, validated_data)


class BookingSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="gym_class.name", read_only=True)
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all(), required=False)

    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["booked_at"]

    def validate(self, attrs):
        if not attrs.get("member") and self.context["request"].user.role != User.Role.MEMBER:
            raise serializers.ValidationError({"member": "This field is required."})
        gym_class = attrs.get("gym_class")
        if gym_class and gym_class.starts_at <= timezone.now():
            raise serializers.ValidationError({"gym_class": "Bookings are only available for upcoming classes."})
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            gym_class = GymClass.objects.select_for_update().get(pk=validated_data["gym_class"].pk)
            member = validated_data["member"]
            if member.memberships.filter(
                status="active", start_date__lte=timezone.localdate(), end_date__gte=timezone.localdate()
            ).exists() is False:
                raise serializers.ValidationError({"member": "An active membership is required to book a class."})
            if gym_class.bookings.filter(member=member).exists():
                raise serializers.ValidationError({"member": "This member already has a booking for this class."})
            if gym_class.bookings.filter(status=Booking.Status.BOOKED).count() >= gym_class.capacity:
                raise serializers.ValidationError({"gym_class": "This class is fully booked."})
            validated_data["gym_class"] = gym_class
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            target_class = validated_data.get("gym_class", instance.gym_class)
            gym_class = GymClass.objects.select_for_update().get(pk=target_class.pk)
            member = validated_data.get("member", instance.member)
            new_status = validated_data.get("status", instance.status)
            if new_status == Booking.Status.BOOKED:
                if gym_class.starts_at <= timezone.now():
                    raise serializers.ValidationError({"gym_class": "Bookings are only available for upcoming classes."})
                if not member.memberships.filter(
                    status=Membership.Status.ACTIVE,
                    start_date__lte=timezone.localdate(),
                    end_date__gte=timezone.localdate(),
                ).exists():
                    raise serializers.ValidationError({"member": "An active membership is required to book a class."})
                duplicate = gym_class.bookings.filter(member=member).exclude(pk=instance.pk)
                if duplicate.exists():
                    raise serializers.ValidationError({"member": "This member already has a booking for this class."})
            if new_status == Booking.Status.BOOKED and (
                instance.status != Booking.Status.BOOKED
                or gym_class.pk != instance.gym_class_id
                or member.pk != instance.member_id
            ):
                booked_query = gym_class.bookings.filter(status=Booking.Status.BOOKED)
                if gym_class.pk == instance.gym_class_id:
                    booked_query = booked_query.exclude(pk=instance.pk)
                booked = booked_query.count()
                if booked >= gym_class.capacity:
                    raise serializers.ValidationError({"status": "This class is fully booked."})
            validated_data["gym_class"] = gym_class
            return super().update(instance, validated_data)


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = "__all__"


class FeedbackSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all(), required=False)

    class Meta:
        model = Feedback
        fields = "__all__"
        read_only_fields = ["created_at"]


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"
        read_only_fields = ["created_by"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["recipient", "created_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = ["id", "actor_name", "action", "object_type", "object_id", "details", "created_at"]


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data.pop("phone", "")
        user = User.objects.create_user(role=User.Role.MEMBER, **validated_data)
        member = Member.objects.create(user=user, phone=phone)
        return member

    def to_representation(self, instance):
        return {
            "id": instance.pk,
            "username": instance.user.username,
            "email": instance.user.email,
            "role": instance.user.role,
            "qr_id": str(instance.qr_id),
        }
