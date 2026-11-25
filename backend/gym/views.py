import csv
import logging
import os
from datetime import timedelta
from io import BytesIO
from pathlib import Path

import requests
from django.db import DatabaseError, transaction
from django.http import FileResponse, Http404, HttpResponse
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Announcement, Attendance, AuditLog, Booking, Equipment, Exercise, Feedback,
    FitnessProgress, GymClass, MealPlan, Member, Membership, Notification,
    NutritionLog, Package, Payment, Staff, User, WorkoutLog, WorkoutPlan,
)
from .permissions import RolePermission
from .serializers import (
    AnnouncementSerializer, AttendanceSerializer, AuditLogSerializer, BookingSerializer,
    EquipmentSerializer, ExerciseSerializer, FeedbackSerializer, FitnessProgressSerializer,
    GymClassSerializer, MealPlanSerializer, MemberSerializer,
    MembershipSerializer, NotificationSerializer, NutritionLogSerializer,
    PackageSerializer, PaymentSerializer, RegistrationSerializer, StaffSerializer,
    WorkoutLogSerializer, WorkoutPlanSerializer,
)

ADMIN = {User.Role.ADMIN}
STAFF = {User.Role.ADMIN, User.Role.RECEPTIONIST}
COACHES = {User.Role.ADMIN, User.Role.TRAINER}
OPERATIONS = {User.Role.ADMIN, User.Role.RECEPTIONIST, User.Role.TRAINER}
ALL_ROLES = {choice[0] for choice in User.Role.choices}
logger = logging.getLogger(__name__)


def current_member(user):
    if user.role != User.Role.MEMBER:
        return None
    try:
        return user.member_profile
    except Member.DoesNotExist:
        return None


class AuditedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RolePermission]
    search_fields = []
    ordering_fields = ["id"]

    def audit(self, obj, action):
        AuditLog.objects.create(
            actor=self.request.user, action=action, object_type=obj._meta.label,
            object_id=obj.pk,
        )

    def perform_create(self, serializer):
        obj = serializer.save()
        self.audit(obj, "create")

    def perform_update(self, serializer):
        obj = serializer.save()
        self.audit(obj, "update")

    def perform_destroy(self, instance):
        self.audit(instance, "delete")
        instance.delete()


class MemberViewSet(AuditedModelViewSet):
    queryset = Member.objects.select_related("user").order_by("id")
    serializer_class = MemberSerializer
    read_roles = ALL_ROLES
    write_roles = STAFF
    search_fields = ["user__first_name", "user__last_name", "user__email", "phone"]
    filterset_fields = ["active", "joined_at"]
    ordering_fields = ["joined_at", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(pk=member.pk)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(workouts__trainer__user=self.request.user).distinct()
        return qs

    def perform_update(self, serializer):
        if self.request.user.role == User.Role.MEMBER and serializer.validated_data.get("user"):
            serializer.validated_data.pop("user")
        super().perform_update(serializer)

    @action(detail=True, methods=["get"])
    def photo(self, request, pk=None):
        return self._file_response(self.get_object(), "photo")

    @action(detail=True, methods=["get"])
    def document(self, request, pk=None):
        return self._file_response(self.get_object(), "document", attachment=True)

    def _file_response(self, member, field_name, attachment=False):
        file = getattr(member, field_name)
        if not file:
            raise Http404("This member file is not available.")
        AuditLog.objects.create(
            actor=self.request.user, action="file_download", object_type=member._meta.label,
            object_id=member.pk, details={"field": field_name},
        )
        return FileResponse(
            file.open("rb"),
            as_attachment=attachment,
            filename=Path(file.name).name,
        )


class StaffViewSet(AuditedModelViewSet):
    queryset = Staff.objects.select_related("user")
    serializer_class = StaffSerializer
    read_roles = {User.Role.ADMIN, User.Role.RECEPTIONIST, User.Role.TRAINER}
    write_roles = ADMIN
    search_fields = ["user__first_name", "user__last_name", "title", "specialties"]
    filterset_fields = ["active", "title"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(user=self.request.user)
        return qs


class PackageViewSet(AuditedModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    read_roles = ALL_ROLES
    write_roles = ADMIN
    search_fields = ["name", "description"]
    filterset_fields = ["active"]
    ordering_fields = ["price", "duration_days", "name"]


class MembershipViewSet(AuditedModelViewSet):
    queryset = Membership.objects.select_related("member__user", "package")
    serializer_class = MembershipSerializer
    read_roles = OPERATIONS | {User.Role.MEMBER}
    write_roles = STAFF
    search_fields = ["member__user__first_name", "member__user__last_name", "package__name"]
    filterset_fields = ["status", "package", "start_date", "end_date"]
    ordering_fields = ["start_date", "end_date", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(member__workouts__trainer__user=self.request.user).distinct()
        return qs

    @action(detail=True, methods=["post"])
    def freeze(self, request, pk=None):
        membership = self.get_object()
        try:
            days = int(request.data.get("days", 0))
        except (TypeError, ValueError):
            days = 0
        if not 1 <= days <= 30:
            return Response({"days": "Choose a freeze period from 1 to 30 days."}, status=400)
        if membership.status != Membership.Status.ACTIVE:
            return Response({"detail": "Only active memberships can be frozen."}, status=400)
        membership.end_date += timedelta(days=days)
        membership.frozen_until = timezone.localdate() + timedelta(days=days)
        membership.status = Membership.Status.FROZEN
        membership.save(update_fields=["end_date", "frozen_until", "status"])
        AuditLog.objects.create(
            actor=request.user, action="freeze", object_type=membership._meta.label,
            object_id=membership.pk, details={"days": days},
        )
        return Response(self.get_serializer(membership).data)

    @action(detail=True, methods=["post"])
    def unfreeze(self, request, pk=None):
        membership = self.get_object()
        if membership.status != Membership.Status.FROZEN:
            return Response({"detail": "This membership is not frozen."}, status=400)
        membership.status = Membership.Status.ACTIVE
        membership.frozen_until = None
        membership.save(update_fields=["status", "frozen_until"])
        AuditLog.objects.create(
            actor=request.user, action="unfreeze", object_type=membership._meta.label,
            object_id=membership.pk,
        )
        return Response(self.get_serializer(membership).data)

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        membership = self.get_object()
        package_id = request.data.get("package", membership.package_id)
        try:
            package = Package.objects.get(pk=package_id, active=True)
        except (Package.DoesNotExist, ValueError, TypeError):
            return Response({"package": "Choose an active membership package."}, status=400)
        start = max(membership.end_date + timedelta(days=1), timezone.localdate())
        renewed = Membership.objects.create(
            member=membership.member, package=package, start_date=start,
            end_date=start + timedelta(days=package.duration_days - 1),
        )
        AuditLog.objects.create(
            actor=request.user, action="renew", object_type=renewed._meta.label,
            object_id=renewed.pk, details={"previous_membership": membership.pk},
        )
        return Response(self.get_serializer(renewed).data, status=status.HTTP_201_CREATED)


class PaymentViewSet(AuditedModelViewSet):
    queryset = Payment.objects.select_related("member__user", "membership")
    serializer_class = PaymentSerializer
    read_roles = STAFF | {User.Role.MEMBER}
    write_roles = STAFF
    search_fields = ["member__user__first_name", "member__user__last_name", "reference"]
    filterset_fields = ["method", "paid_at", "membership"]
    ordering_fields = ["paid_at", "amount"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        return qs.filter(member=member) if member else qs

    @action(detail=True, methods=["get"])
    def receipt(self, request, pk=None):
        payment = self.get_object()
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        output = BytesIO()
        document = canvas.Canvas(output, pagesize=letter)
        document.setTitle(f"FitHub Elite receipt {payment.pk}")
        document.setFont("Helvetica-Bold", 20)
        document.drawString(54, 735, "FitHub Elite")
        document.setFont("Helvetica", 12)
        document.drawString(54, 700, "PAYMENT RECEIPT")
        document.drawString(54, 670, f"Receipt: FH-{payment.pk:06d}")
        document.drawString(54, 648, f"Member: {payment.member.user.get_full_name()} ({payment.member.user.email})")
        document.drawString(54, 626, f"Date: {payment.paid_at:%Y-%m-%d %H:%M UTC}")
        document.drawString(54, 604, f"Payment method: {payment.get_method_display()}")
        document.drawString(54, 582, f"Reference: {payment.reference or '—'}")
        document.drawString(54, 548, f"Amount paid: {payment.amount}")
        if payment.membership_id:
            document.drawString(
                54, 526, f"Membership: {payment.membership.package.name} ({payment.membership.start_date} to {payment.membership.end_date})"
            )
        document.save()
        response = HttpResponse(output.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="receipt-{payment.pk}.pdf"'
        self.audit(payment, "receipt")
        return response


class AttendanceViewSet(AuditedModelViewSet):
    queryset = Attendance.objects.select_related("member__user", "recorded_by")
    serializer_class = AttendanceSerializer
    read_roles = ALL_ROLES
    write_roles = STAFF
    search_fields = ["member__user__first_name", "member__user__last_name"]
    filterset_fields = ["checked_in_at", "member"]
    ordering_fields = ["checked_in_at", "checked_out_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(member__workouts__trainer__user=self.request.user).distinct()
        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
        self.audit(serializer.instance, "create")


class WorkoutPlanViewSet(AuditedModelViewSet):
    queryset = WorkoutPlan.objects.select_related("member__user", "trainer__user")
    serializer_class = WorkoutPlanSerializer
    read_roles = ALL_ROLES
    write_roles = COACHES
    search_fields = ["name", "member__user__first_name", "member__user__last_name"]
    filterset_fields = ["member", "trainer", "active"]
    ordering_fields = ["start_date", "end_date"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(trainer__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == User.Role.TRAINER:
            self.audit(serializer.save(trainer=Staff.objects.get(user=self.request.user)), "create")
        else:
            super().perform_create(serializer)

    def perform_update(self, serializer):
        member = current_member(self.request.user)
        if member:
            serializer.validated_data.pop("resolved", None)
            self.audit(serializer.save(member=member), "update")
        else:
            super().perform_update(serializer)

    def perform_update(self, serializer):
        if self.request.user.role == User.Role.TRAINER:
            self.audit(serializer.save(trainer=Staff.objects.get(user=self.request.user)), "update")
        else:
            super().perform_update(serializer)


class WorkoutLogViewSet(AuditedModelViewSet):
    queryset = WorkoutLog.objects.select_related("member__user", "plan").order_by("id")
    serializer_class = WorkoutLogSerializer
    read_roles = ALL_ROLES
    write_roles = COACHES | {User.Role.MEMBER}
    search_fields = ["exercise_name", "member__user__first_name", "member__user__last_name"]
    filterset_fields = ["member", "plan", "performed_at"]
    ordering_fields = ["performed_at", "exercise_name", "weight_kg"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(member__workouts__trainer__user=self.request.user).distinct()
        return qs

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if current_member(self.request.user):
            fields = serializer.child.fields if getattr(serializer, "many", False) else serializer.fields
            fields["member"].read_only = True
        return serializer

    def perform_create(self, serializer):
        member = current_member(self.request.user)
        if member:
            self.audit(serializer.save(member=member), "create")
        else:
            if self.request.user.role == User.Role.TRAINER and not WorkoutPlan.objects.filter(
                member=serializer.validated_data["member"], trainer__user=self.request.user
            ).exists():
                raise ValidationError({"member": "Assign this member to a workout plan before logging training."})
            super().perform_create(serializer)

    def perform_update(self, serializer):
        member = current_member(self.request.user)
        if member:
            self.audit(serializer.save(member=member), "update")
        else:
            if self.request.user.role == User.Role.TRAINER and not WorkoutPlan.objects.filter(
                member=serializer.validated_data.get("member", serializer.instance.member),
                trainer__user=self.request.user,
            ).exists():
                raise ValidationError({"member": "This member is not assigned to you."})
            super().perform_update(serializer)


class ExerciseViewSet(AuditedModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    read_roles = ALL_ROLES
    write_roles = COACHES
    search_fields = ["name", "muscle_group", "equipment"]
    filterset_fields = ["muscle_group"]
    ordering_fields = ["name", "muscle_group"]

class MealPlanViewSet(AuditedModelViewSet):
    queryset = MealPlan.objects.select_related("member__user", "trainer__user")
    serializer_class = MealPlanSerializer
    read_roles = ALL_ROLES
    write_roles = COACHES
    search_fields = ["name", "member__user__first_name", "member__user__last_name"]
    filterset_fields = ["member", "trainer"]
    ordering_fields = ["start_date", "daily_calories"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(trainer__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == User.Role.TRAINER:
            self.audit(serializer.save(trainer=Staff.objects.get(user=self.request.user)), "create")
        else:
            super().perform_create(serializer)

    def perform_update(self, serializer):
        if self.request.user.role == User.Role.TRAINER:
            self.audit(serializer.save(trainer=Staff.objects.get(user=self.request.user)), "update")
        else:
            super().perform_update(serializer)


class NutritionLogViewSet(AuditedModelViewSet):
    queryset = NutritionLog.objects.select_related("member__user").order_by("id")
    serializer_class = NutritionLogSerializer
    read_roles = ALL_ROLES
    write_roles = OPERATIONS | {User.Role.MEMBER}
    search_fields = ["meal_name", "member__user__first_name", "member__user__last_name"]
    filterset_fields = ["member", "logged_at"]
    ordering_fields = ["logged_at", "calories"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(member__workouts__trainer__user=self.request.user).distinct()
        return qs

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if current_member(self.request.user):
            fields = serializer.child.fields if getattr(serializer, "many", False) else serializer.fields
            fields["member"].read_only = True
        return serializer

    def perform_create(self, serializer):
        member = current_member(self.request.user)
        if member:
            self.audit(serializer.save(member=member), "create")
        else:
            if self.request.user.role == User.Role.TRAINER and not WorkoutPlan.objects.filter(
                member=serializer.validated_data["member"], trainer__user=self.request.user
            ).exists():
                raise ValidationError({"member": "Assign this member to a workout plan before recording nutrition."})
            super().perform_create(serializer)

    def perform_update(self, serializer):
        member = current_member(self.request.user)
        if member:
            self.audit(serializer.save(member=member), "update")
        else:
            if self.request.user.role == User.Role.TRAINER and not WorkoutPlan.objects.filter(
                member=serializer.validated_data.get("member", serializer.instance.member),
                trainer__user=self.request.user,
            ).exists():
                raise ValidationError({"member": "This member is not assigned to you."})
            super().perform_update(serializer)


class FitnessProgressViewSet(AuditedModelViewSet):
    queryset = FitnessProgress.objects.select_related("member__user").order_by("recorded_at")
    serializer_class = FitnessProgressSerializer
    read_roles = ALL_ROLES
    write_roles = OPERATIONS
    search_fields = ["member__user__first_name", "member__user__last_name", "goal"]
    filterset_fields = ["member", "recorded_at"]
    ordering_fields = ["recorded_at", "weight_kg"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(member__workouts__trainer__user=self.request.user).distinct()
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == User.Role.TRAINER and not WorkoutPlan.objects.filter(
            member=serializer.validated_data["member"], trainer__user=self.request.user
        ).exists():
            raise ValidationError({"member": "This member is not assigned to you."})
        super().perform_create(serializer)

    @action(detail=True, methods=["get"])
    def photo(self, request, pk=None):
        progress = self.get_object()
        if not progress.photo:
            raise Http404("This progress photo is not available.")
        AuditLog.objects.create(
            actor=request.user, action="file_download", object_type=progress._meta.label,
            object_id=progress.pk, details={"field": "photo"},
        )
        return FileResponse(
            progress.photo.open("rb"),
            as_attachment=False,
            filename=Path(progress.photo.name).name,
        )


class GymClassViewSet(AuditedModelViewSet):
    queryset = GymClass.objects.select_related("trainer__user").annotate(_booked_count=Count("bookings"))
    serializer_class = GymClassSerializer
    read_roles = ALL_ROLES
    write_roles = STAFF | {User.Role.TRAINER}
    search_fields = ["name", "location", "trainer__user__first_name"]
    filterset_fields = ["trainer", "starts_at"]
    ordering_fields = ["starts_at", "capacity", "name"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(trainer__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        if self.request.user.role == User.Role.TRAINER:
            self.audit(serializer.save(trainer=Staff.objects.get(user=self.request.user)), "create")
        else:
            super().perform_create(serializer)

    def perform_update(self, serializer):
        if self.request.user.role == User.Role.TRAINER:
            self.audit(serializer.save(trainer=Staff.objects.get(user=self.request.user)), "update")
        else:
            super().perform_update(serializer)


class BookingViewSet(AuditedModelViewSet):
    queryset = Booking.objects.select_related("gym_class", "member__user")
    serializer_class = BookingSerializer
    read_roles = ALL_ROLES
    write_roles = OPERATIONS | {User.Role.MEMBER}
    search_fields = ["gym_class__name", "member__user__first_name", "member__user__last_name"]
    filterset_fields = ["gym_class", "member", "status"]
    ordering_fields = ["booked_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        if member:
            return qs.filter(member=member)
        if self.request.user.role == User.Role.TRAINER:
            return qs.filter(gym_class__trainer__user=self.request.user)
        return qs

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if current_member(self.request.user):
            fields = serializer.child.fields if getattr(serializer, "many", False) else serializer.fields
            fields["member"].read_only = True
        return serializer

    def perform_create(self, serializer):
        member = current_member(self.request.user)
        if member:
            serializer.save(member=member)
            self.audit(serializer.instance, "create")
        else:
            super().perform_create(serializer)

    def perform_update(self, serializer):
        member = current_member(self.request.user)
        if member:
            if serializer.validated_data.get("status") == Booking.Status.ATTENDED:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Members cannot mark a booking as attended.")
            self.audit(serializer.save(member=member), "update")
        else:
            super().perform_update(serializer)


class EquipmentViewSet(AuditedModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    read_roles = STAFF | {User.Role.TRAINER}
    write_roles = STAFF
    search_fields = ["name", "inventory_code"]
    filterset_fields = ["status"]
    ordering_fields = ["name", "quantity", "maintenance_due"]


class FeedbackViewSet(AuditedModelViewSet):
    queryset = Feedback.objects.select_related("member__user")
    serializer_class = FeedbackSerializer
    read_roles = STAFF | {User.Role.MEMBER}
    write_roles = STAFF | {User.Role.MEMBER}
    search_fields = ["message", "member__user__first_name"]
    filterset_fields = ["resolved", "rating"]
    ordering_fields = ["created_at", "rating"]

    def get_queryset(self):
        qs = super().get_queryset()
        member = current_member(self.request.user)
        return qs.filter(member=member) if member else qs

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if current_member(self.request.user):
            fields = serializer.child.fields if getattr(serializer, "many", False) else serializer.fields
            fields["member"].read_only = True
        return serializer

    def perform_create(self, serializer):
        member = current_member(self.request.user)
        if member:
            serializer.save(member=member)
        else:
            super().perform_create(serializer)


class AnnouncementViewSet(AuditedModelViewSet):
    queryset = Announcement.objects.select_related("created_by")
    serializer_class = AnnouncementSerializer
    read_roles = ALL_ROLES
    write_roles = STAFF
    search_fields = ["title", "message"]
    filterset_fields = ["audience", "published_at"]
    ordering_fields = ["published_at", "expires_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == User.Role.MEMBER:
            qs = qs.filter(audience__in=["", User.Role.MEMBER])
        elif self.request.user.role != User.Role.ADMIN:
            qs = qs.filter(audience__in=["", self.request.user.role])
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class NotificationViewSet(AuditedModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    read_roles = ALL_ROLES
    write_roles = ADMIN
    search_fields = ["title", "message"]
    filterset_fields = ["read_at"]
    ordering_fields = ["created_at"]
    action_write_roles = {"mark_read": ALL_ROLES}

    def get_queryset(self):
        return super().get_queryset().filter(recipient=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response(self.get_serializer(notification).data)


class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.pk,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
        })


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("actor")
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = ADMIN
    serializer_class = AuditLogSerializer
    search_fields = ["action", "object_type", "actor__username"]
    ordering_fields = ["created_at", "action"]


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        member = current_member(request.user)
        payments = Payment.objects.all()
        attendance = Attendance.objects.all()
        memberships = Membership.objects.all()
        if member:
            payments = payments.filter(member=member)
            attendance = attendance.filter(member=member)
            memberships = memberships.filter(member=member)
        elif request.user.role == User.Role.TRAINER:
            assigned_members = Member.objects.filter(
                workouts__trainer__user=request.user
            ).distinct()
            payments = payments.filter(member__in=assigned_members)
            attendance = attendance.filter(member__in=assigned_members)
            memberships = memberships.filter(member__in=assigned_members)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        revenue = payments.filter(
            paid_at__date__gte=month_start, paid_at__date__lte=today
        ).aggregate(total=Sum("amount"))["total"] or 0
        recent = payments.order_by("-paid_at")[:6]
        attendance_today = attendance.filter(checked_in_at__date=today).count()
        active_memberships = memberships.filter(status=Membership.Status.ACTIVE, end_date__gte=today).count()
        data = {
            "revenue_this_month": revenue,
            "attendance_today": attendance_today,
            "active_memberships": active_memberships,
            "expiring_memberships": memberships.filter(
                status=Membership.Status.ACTIVE, end_date__range=(today, today + timedelta(days=7))
            ).count(),
            "recent_payments": [
                {"id": payment.id, "member": payment.member.user.get_full_name(), "amount": payment.amount,
                 "paid_at": payment.paid_at, "method": payment.method}
                for payment in recent
            ],
            "attendance_week": [
                {
                    "date": (today - timedelta(days=offset)).isoformat(),
                    "visits": attendance.filter(
                        checked_in_at__date=today - timedelta(days=offset)
                    ).count(),
                }
                for offset in range(6, -1, -1)
            ],
        }
        if not member:
            revenue_months = []
            for offset in range(5, -1, -1):
                month_index = month_start.year * 12 + month_start.month - 1 - offset
                year, month_number = divmod(month_index, 12)
                month = month_start.replace(year=year, month=month_number + 1)
                next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
                total = payments.filter(
                    paid_at__date__gte=month, paid_at__date__lt=next_month
                ).aggregate(total=Sum("amount"))["total"] or 0
                revenue_months.append({"month": month.strftime("%b"), "revenue": total})
            member_queryset = Member.objects.filter(active=True)
            class_queryset = GymClass.objects.filter(starts_at__gte=timezone.now())
            if request.user.role == User.Role.TRAINER:
                member_queryset = member_queryset.filter(workouts__trainer__user=request.user).distinct()
                class_queryset = class_queryset.filter(trainer__user=request.user)
            data["total_members"] = member_queryset.count()
            data["revenue_months"] = revenue_months
            data["equipment_attention"] = Equipment.objects.filter(
                Q(status=Equipment.Status.MAINTENANCE) | Q(maintenance_due__lte=today)
            ).count()
            data["upcoming_classes"] = class_queryset.order_by("starts_at")[:5].values(
                "id", "name", "starts_at", "location"
            )
        return Response(data)


class AttendanceCheckInView(APIView):
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = STAFF
    write_roles = STAFF

    def post(self, request):
        qr_id = request.data.get("qr_id")
        if not qr_id:
            return Response({"qr_id": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            member = Member.objects.select_related("user").get(qr_id=qr_id, active=True)
        except (Member.DoesNotExist, ValueError):
            return Response({"detail": "No active member matches this QR ID."}, status=status.HTTP_404_NOT_FOUND)
        today = timezone.localdate()
        if not member.memberships.filter(
            status=Membership.Status.ACTIVE, start_date__lte=today, end_date__gte=today
        ).exists():
            return Response({"detail": "This member has no active membership."}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            member = Member.objects.select_for_update().get(pk=member.pk)
            open_visit = Attendance.objects.filter(
                member=member, checked_out_at__isnull=True
            ).order_by("-checked_in_at").first()
            if open_visit:
                open_visit.checked_out_at = timezone.now()
                open_visit.save(update_fields=["checked_out_at"])
                AuditLog.objects.create(
                    actor=request.user, action="check_out", object_type=Attendance._meta.label,
                    object_id=open_visit.pk, details={"member": member.pk},
                )
                return Response({"action": "check_out", "attendance_id": open_visit.id})
            visit = Attendance.objects.create(member=member, recorded_by=request.user, source="qr")
            AuditLog.objects.create(
                actor=request.user, action="check_in", object_type=Attendance._meta.label,
                object_id=visit.pk, details={"member": member.pk},
            )
        return Response({"action": "check_in", "attendance_id": visit.id}, status=status.HTTP_201_CREATED)


class AIAdviceView(APIView):
    permission_classes = [IsAuthenticated]
    MAX_PROMPT_LENGTH = 4000

    def post(self, request):
        prompt = request.data.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > self.MAX_PROMPT_LENGTH:
            return Response(
                {"prompt": f"Provide a prompt containing 1 to {self.MAX_PROMPT_LENGTH} characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        if not api_key:
            return Response(
                {"detail": "AI assistance is unavailable. Configure MISTRAL_API_KEY on the backend."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            result = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "codestral-latest",
                    "messages": [
                        {"role": "system", "content": "You are a fitness assistant. Give practical, safe, general wellness guidance. Avoid medical diagnosis and advise professional care for medical concerns."},
                        {"role": "user", "content": prompt.strip()},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 900,
                },
                timeout=(5, 30),
            )
            result.raise_for_status()
            answer = result.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            return Response(
                {"detail": "Mistral could not complete the request. Please try again later."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"answer": answer, "model": "codestral-latest"})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_health(request):
    try:
        User.objects.exists()
    except DatabaseError:
        logger.exception("Database readiness check failed.")
        return Response(
            {"status": "unavailable", "database": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        "name": "FitHub Elite API",
        "status": "ok",
        "health": "/api/health/",
    })


class ExportView(APIView):
    permission_classes = [IsAuthenticated, RolePermission]
    read_roles = STAFF
    write_roles = ADMIN
    EXPORTS = {
        "members": (Member, ("id", "user__first_name", "user__last_name", "user__email", "phone", "joined_at", "active")),
        "payments": (Payment, ("id", "member__user__email", "amount", "method", "reference", "paid_at")),
        "attendance": (Attendance, ("id", "member__user__email", "checked_in_at", "checked_out_at", "source")),
        "memberships": (Membership, ("id", "member__user__email", "package__name", "start_date", "end_date", "status")),
    }

    def get(self, request, resource):
        if resource not in self.EXPORTS:
            return Response({"detail": "Export is not available for this resource."}, status=status.HTTP_404_NOT_FOUND)
        output_format = request.query_params.get("output", "csv").lower()
        if output_format not in {"csv", "excel", "pdf"}:
            return Response({"format": "Choose csv, excel, or pdf."}, status=status.HTTP_400_BAD_REQUEST)
        model, fields = self.EXPORTS[resource]
        queryset = model.objects.all()
        values = list(queryset.values_list(*fields).iterator())
        if output_format == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{resource}.csv"'
            writer = csv.writer(response)
            writer.writerow(fields)
            writer.writerows([[_spreadsheet_safe(value) for value in row] for row in values])
        elif output_format == "excel":
            from openpyxl import Workbook

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = resource.title()
            sheet.append(fields)
            for row in values:
                sheet.append([_spreadsheet_safe(value) for value in row])
            output = BytesIO()
            workbook.save(output)
            response = HttpResponse(
                output.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f'attachment; filename="{resource}.xlsx"'
        else:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

            output = BytesIO()
            document = SimpleDocTemplate(output, pagesize=landscape(letter))
            table = Table([fields, *[[_spreadsheet_safe(value) for value in row] for row in values]], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#163b2a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce4dc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6f2")]),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            document.build([table])
            response = HttpResponse(output.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{resource}.pdf"'
        AuditLog.objects.create(
            actor=request.user, action="export", object_type=resource, object_id="all",
        )
        return response


def _spreadsheet_safe(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value}"
    return value
