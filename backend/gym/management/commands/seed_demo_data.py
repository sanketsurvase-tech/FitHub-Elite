from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from gym.models import (
    Announcement,
    Attendance,
    Booking,
    Equipment,
    Exercise,
    Feedback,
    FitnessProgress,
    GymClass,
    MealPlan,
    Member,
    Membership,
    Notification,
    NutritionLog,
    Package,
    Payment,
    Staff,
    User,
    WorkoutLog,
    WorkoutPlan,
)


FIRST_NAMES = [
    "Avery", "Blake", "Cameron", "Dakota", "Emerson", "Finley", "Harper",
    "Jamie", "Jordan", "Kai", "Logan", "Morgan", "Parker", "Quinn",
    "Reese", "Riley", "Rowan", "Sage", "Taylor", "Val",
]
LAST_NAMES = [
    "Adams", "Bennett", "Carter", "Diaz", "Ellis", "Foster", "Garcia",
    "Hayes", "Ibrahim", "James", "Kim", "Lopez", "Miller", "Nguyen",
    "Owens", "Patel", "Reed", "Singh", "Turner", "Wright",
]
EXERCISES = [
    ("[DEMO] Goblet squat", "Legs", "Dumbbell"),
    ("[DEMO] Romanian deadlift", "Legs", "Barbell"),
    ("[DEMO] Dumbbell bench press", "Chest", "Dumbbell"),
    ("[DEMO] Lat pulldown", "Back", "Cable"),
    ("[DEMO] Seated cable row", "Back", "Cable"),
    ("[DEMO] Overhead press", "Shoulders", "Dumbbell"),
    ("[DEMO] Walking lunge", "Legs", "Bodyweight"),
    ("[DEMO] Plank", "Core", "Bodyweight"),
    ("[DEMO] Kettlebell swing", "Full body", "Kettlebell"),
    ("[DEMO] Incline push-up", "Chest", "Bodyweight"),
]
PACKAGES = [
    ("[DEMO] Monthly", 30, "49.00"),
    ("[DEMO] Quarterly", 90, "129.00"),
    ("[DEMO] Half-year", 180, "239.00"),
    ("[DEMO] Annual", 365, "449.00"),
    ("[DEMO] Student monthly", 30, "35.00"),
]
CLASS_NAMES = [
    "Strength Circuit", "Morning Yoga", "Spin Express", "Mobility Flow",
    "HIIT Fundamentals", "Pilates Core", "Boxing Fitness", "Full Body Conditioning",
]
MEAL_CHOICES = [
    ("Breakfast", 420, 28, 52, 12, "Oats, yogurt, berries"),
    ("Lunch", 610, 42, 68, 18, "Chicken, rice, mixed vegetables"),
    ("Dinner", 540, 38, 46, 20, "Salmon, potatoes, greens"),
    ("Snack", 260, 18, 30, 8, "Cottage cheese and fruit"),
]


class Command(BaseCommand):
    help = "Create clearly labeled, repeatable demo records across gym modules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--members",
            type=int,
            default=100,
            help="Number of demo members to create (1-500; default: 100).",
        )

    def handle(self, *args, **options):
        member_count = options["members"]
        if not 1 <= member_count <= 500:
            raise CommandError("--members must be between 1 and 500.")

        admin_user = User.objects.filter(is_superuser=True).order_by("pk").first()
        if admin_user is None:
            raise CommandError("Create an administrator before seeding demo data.")

        self.created = defaultdict(int)
        with transaction.atomic():
            trainers = self._trainers()
            packages = self._packages()
            exercises = self._exercises()
            members = self._members(member_count)
            self._memberships_and_payments(members, packages)
            self._attendance(members, admin_user)
            self._workout_and_meal_plans(members, trainers, exercises)
            self._progress_and_nutrition(members)
            classes = self._classes(trainers)
            self._bookings(members, classes)
            self._equipment()
            self._feedback_and_notifications(members)
            self._announcements(admin_user)

        created_summary = ", ".join(
            f"{count} {model_name}"
            for model_name, count in sorted(self.created.items())
            if count
        )
        self.stdout.write(self.style.SUCCESS(
            f"Demo seed complete. Created: {created_summary or 'no new rows; existing demo data is intact.'}"
        ))
        self.stdout.write(
            "Demo member usernames use demo.member.NNNN; those accounts have no usable password."
        )

    def _record(self, model, lookup, defaults):
        instance, created = model.objects.get_or_create(**lookup, defaults=defaults)
        if created:
            self.created[model.__name__] += 1
        return instance

    def _demo_user(self, username, email, first_name, last_name, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
            self.created[User.__name__] += 1
        if user.email != email or user.role != role:
            raise CommandError(
                f"Existing account {username!r} does not match the expected demo account; no records were changed."
            )
        if user.has_usable_password():
            raise CommandError(
                f"Existing demo account {username!r} has a usable password; no records were changed."
            )
        return user

    def _trainers(self):
        trainers = []
        specialties = [
            "Strength and conditioning",
            "Mobility and recovery",
            "Cardio and endurance",
            "General fitness",
        ]
        for index, specialty in enumerate(specialties, start=1):
            user = self._demo_user(
                f"demo.trainer.{index:02d}",
                f"demo.trainer.{index:02d}@example.invalid",
                FIRST_NAMES[index],
                LAST_NAMES[index],
                User.Role.TRAINER,
            )
            trainers.append(self._record(
                Staff,
                {"user": user},
                {
                    "title": f"[DEMO] Trainer {index:02d}",
                    "phone": f"555-02{index:02d}",
                    "specialties": specialty,
                    "schedule": {"days": ["Monday", "Wednesday", "Friday"]},
                },
            ))
        return trainers

    def _packages(self):
        return [
            self._record(
                Package,
                {"name": name},
                {
                    "duration_days": duration,
                    "price": Decimal(price),
                    "description": "[DEMO] Synthetic package for demonstration.",
                },
            )
            for name, duration, price in PACKAGES
        ]

    def _exercises(self):
        return [
            self._record(
                Exercise,
                {"name": name},
                {
                    "muscle_group": muscle_group,
                    "equipment": equipment,
                    "instructions": "[DEMO] Example exercise entry.",
                },
            )
            for name, muscle_group, equipment in EXERCISES
        ]

    def _members(self, member_count):
        today = timezone.localdate()
        usernames = [f"demo.member.{index:04d}" for index in range(1, member_count + 1)]
        existing_users = {
            user.username: user
            for user in User.objects.filter(username__in=usernames)
        }
        new_users = []
        for index in range(1, member_count + 1):
            username = f"demo.member.{index:04d}"
            email = f"{username.replace('.', '')}@example.invalid"
            user = existing_users.get(username)
            if user:
                if user.email != email or user.role != User.Role.MEMBER:
                    raise CommandError(
                        f"Existing account {username!r} does not match the expected demo account; no records were changed."
                    )
                if user.has_usable_password():
                    raise CommandError(
                        f"Existing demo account {username!r} has a usable password; no records were changed."
                    )
                continue
            user = User(
                username=username,
                email=email,
                first_name=FIRST_NAMES[(index - 1) % len(FIRST_NAMES)],
                last_name=LAST_NAMES[((index - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)],
                role=User.Role.MEMBER,
            )
            user.set_unusable_password()
            new_users.append(user)

        User.objects.bulk_create(new_users, batch_size=500)
        self.created[User.__name__] += len(new_users)
        all_users = {
            user.username: user
            for user in User.objects.filter(username__in=usernames)
        }
        existing_members = {
            member.user_id: member
            for member in Member.objects.filter(user__in=all_users.values())
        }
        new_members = []
        for index, username in enumerate(usernames, start=1):
            user = all_users[username]
            if user.pk in existing_members:
                continue
            new_members.append(Member(
                user=user,
                phone=f"555-{1000 + index:04d}",
                joined_at=today - timedelta(days=(index * 7) % 700),
                emergency_contact_name="[DEMO] Emergency Contact",
                emergency_contact_phone=f"555-{3000 + index:04d}",
                active=index % 17 != 0,
            ))
        Member.objects.bulk_create(new_members, batch_size=500)
        self.created[Member.__name__] += len(new_members)
        return new_members

    def _memberships_and_payments(self, members, packages):
        today = timezone.localdate()
        statuses = list(Membership.Status.values)
        methods = list(Payment.Method.values)
        memberships = []
        payments = []
        for index, member in enumerate(members, start=1):
            package = packages[(index - 1) % len(packages)]
            status_value = statuses[(index - 1) % len(statuses)]
            if status_value == Membership.Status.EXPIRED:
                end_date = today - timedelta(days=1 + index % 60)
                start_date = end_date - timedelta(days=package.duration_days)
                frozen_until = None
            else:
                start_date = today - timedelta(days=index % 45)
                end_date = start_date + timedelta(days=package.duration_days)
                frozen_until = (
                    today + timedelta(days=3 + index % 14)
                    if status_value == Membership.Status.FROZEN
                    else None
                )
            membership = Membership(
                member=member,
                package=package,
                start_date=start_date,
                **{
                    "end_date": end_date,
                    "status": status_value,
                    "frozen_until": frozen_until,
                    "notes": "[DEMO] Synthetic membership record.",
                },
            )
            memberships.append(membership)
            payments.append(Payment(
                reference=f"[DEMO] PAY-{member.user.username.rsplit('.', 1)[-1]}",
                member=member,
                membership=membership,
                amount=package.price,
                method=methods[(index - 1) % len(methods)],
                notes="[DEMO] Synthetic payment; not a real transaction.",
                paid_at=timezone.now() - timedelta(days=index % 120),
            ))
        Membership.objects.bulk_create(memberships, batch_size=500)
        Payment.objects.bulk_create(payments, batch_size=500)
        self.created[Membership.__name__] += len(memberships)
        self.created[Payment.__name__] += len(payments)

    def _attendance(self, members, admin_user):
        now = timezone.now()
        attendance = []
        for index, member in enumerate(members, start=1):
            for visit in range(2):
                visit_date = timezone.localdate() - timedelta(
                    days=(index + visit * 9) % 30
                )
                check_in = timezone.make_aware(datetime.combine(
                    visit_date, time(hour=6 + (index + visit) % 13, minute=15)
                ))
                attendance.append(Attendance(
                    member=member,
                    checked_in_at=check_in,
                    checked_out_at=check_in + timedelta(minutes=45 + index % 90),
                    source="demo",
                    recorded_by=admin_user,
                ))
        Attendance.objects.bulk_create(attendance, batch_size=500)
        self.created[Attendance.__name__] += len(attendance)

    def _workout_and_meal_plans(self, members, trainers, exercises):
        plans = [
            WorkoutPlan(
                member=member,
                trainer=trainers[(index - 1) % len(trainers)],
                name=f"[DEMO] Training plan {index:04d}",
                details=[
                    {
                        "exercise": exercises[(index + offset - 1) % len(exercises)].name,
                        "sets": 3 + offset % 2,
                        "reps": 8 + (index + offset) % 7,
                        "weight_kg": 10 + (index * 2 + offset * 5) % 80,
                    }
                    for offset in range(4)
                ],
                start_date=timezone.localdate() - timedelta(days=index % 60),
                active=index % 9 != 0,
            )
            for index, member in enumerate(members, start=1)
        ]
        WorkoutPlan.objects.bulk_create(plans, batch_size=500)
        self.created[WorkoutPlan.__name__] += len(plans)

        workout_logs = [
            WorkoutLog(
                member=member,
                plan=plan,
                performed_at=timezone.localdate() - timedelta(days=index % 14),
                exercise_name=exercises[(index - 1) % len(exercises)].name,
                sets=3 + index % 3,
                reps=8 + index % 9,
                weight_kg=Decimal(10 + index % 100),
                notes="[DEMO] Example training log.",
            )
            for index, (member, plan) in enumerate(zip(members, plans), start=1)
        ]
        WorkoutLog.objects.bulk_create(workout_logs, batch_size=500)
        self.created[WorkoutLog.__name__] += len(workout_logs)

        meal_plans = []
        for index, member in enumerate(members, start=1):
            meal = MEAL_CHOICES[(index - 1) % len(MEAL_CHOICES)]
            meal_plans.append(MealPlan(
                member=member,
                trainer=trainers[(index - 1) % len(trainers)],
                name=f"[DEMO] Nutrition plan {index:04d}",
                meals=[{"name": meal[0], "items": meal[5].split(", ")}],
                daily_calories=1800 + index % 1200,
                protein_g=90 + index % 100,
                carbs_g=140 + index % 180,
                fats_g=45 + index % 60,
                start_date=timezone.localdate() - timedelta(days=index % 30),
            ))
        MealPlan.objects.bulk_create(meal_plans, batch_size=500)
        self.created[MealPlan.__name__] += len(meal_plans)
        return plans

    def _progress_and_nutrition(self, members):
        today = timezone.localdate()
        progress = []
        nutrition_logs = []
        for index, member in enumerate(members, start=1):
            weight = Decimal(55 + index % 55)
            height = Decimal(150 + index % 45)
            for checkpoint in range(2):
                recorded_at = today - timedelta(days=checkpoint * 30 + index % 12)
                progress.append(FitnessProgress(
                    member=member,
                    recorded_at=recorded_at,
                    weight_kg=weight + Decimal(checkpoint),
                    height_cm=height,
                    body_fat_percent=Decimal(16 + index % 22),
                    measurements={
                        "chest_cm": 80 + index % 35,
                        "waist_cm": 65 + index % 35,
                        "hips_cm": 85 + index % 35,
                    },
                    goal="[DEMO] Build consistent fitness habits.",
                ))
            meal = MEAL_CHOICES[(index - 1) % len(MEAL_CHOICES)]
            nutrition_logs.append(NutritionLog(
                member=member,
                meal_name=f"[DEMO] {meal[0]}",
                logged_at=today - timedelta(days=index % 14),
                food_entries=[
                    {"name": item, "grams": 100 + index % 200}
                    for item in meal[5].split(", ")
                ],
                calories=meal[1],
                protein_g=meal[2],
                carbs_g=meal[3],
                fats_g=meal[4],
                notes="[DEMO] Synthetic nutrition log.",
            ))
        FitnessProgress.objects.bulk_create(progress, batch_size=500)
        NutritionLog.objects.bulk_create(nutrition_logs, batch_size=500)
        self.created[FitnessProgress.__name__] += len(progress)
        self.created[NutritionLog.__name__] += len(nutrition_logs)


    def _classes(self, trainers):
        now = timezone.now()
        classes = []
        for index in range(1, 21):
            starts_at = now + timedelta(days=index, hours=6 + index % 12)
            ends_at = starts_at + timedelta(minutes=45 + index % 4 * 15)
            classes.append(self._record(
                GymClass,
                {"name": f"[DEMO] {CLASS_NAMES[(index - 1) % len(CLASS_NAMES)]} {index:02d}"},
                {
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                    "trainer": trainers[(index - 1) % len(trainers)],
                    "capacity": 20,
                    "location": f"Studio {(index - 1) % 4 + 1}",
                    "description": "[DEMO] Scheduled sample class.",
                },
            ))
        return classes

    def _bookings(self, members, classes):
        bookings = [
            Booking(
                gym_class=classes[(index - 1) % len(classes)],
                member=member,
                status=list(Booking.Status.values)[(index - 1) % 3],
            )
            for index, member in enumerate(members, start=1)
        ]
        Booking.objects.bulk_create(bookings, batch_size=500)
        self.created[Booking.__name__] += len(bookings)

    def _equipment(self):
        equipment = [
            ("Treadmill", 4), ("Stationary bike", 6), ("Rowing machine", 3),
            ("Squat rack", 5), ("Adjustable bench", 8), ("Cable station", 2),
            ("Kettlebell set", 12), ("Dumbbell set", 10), ("Elliptical", 4),
            ("Leg press", 2), ("Medicine ball set", 9), ("Resistance band set", 15),
            ("Lat pulldown", 3), ("Spin bike", 10), ("Foam roller set", 14),
        ]
        today = timezone.localdate()
        statuses = list(Equipment.Status.values)
        for index, (name, quantity) in enumerate(equipment, start=1):
            last_maintenance = today - timedelta(days=index * 5)
            self._record(
                Equipment,
                {"inventory_code": f"DEMO-EQ-{index:03d}"},
                {
                    "name": f"[DEMO] {name}",
                    "quantity": quantity,
                    "status": statuses[(index - 1) % len(statuses)],
                    "last_maintenance": last_maintenance,
                    "maintenance_due": last_maintenance + timedelta(days=60),
                    "notes": "[DEMO] Synthetic inventory item.",
                },
            )

    def _feedback_and_notifications(self, members):
        feedback = []
        notifications = []
        for index, member in enumerate(members, start=1):
            feedback.append(Feedback(
                member=member,
                message=f"[DEMO] Sample feedback entry {index:04d}.",
                **{
                    "rating": (index - 1) % 5 + 1,
                    "resolved": index % 2 == 0,
                },
            ))
            notifications.append(Notification(
                recipient=member.user,
                title="[DEMO] Welcome to FitHub Elite",
                message="[DEMO] This is a sample in-app notification.",
                read_at=timezone.now() if index % 2 == 0 else None,
            ))
        Feedback.objects.bulk_create(feedback, batch_size=500)
        Notification.objects.bulk_create(notifications, batch_size=500)
        self.created[Feedback.__name__] += len(feedback)
        self.created[Notification.__name__] += len(notifications)

    def _announcements(self, admin_user):
        announcements = [
            ("Welcome", "Explore the equipment and book a class."),
            ("Class schedule", "New sample classes have been added this week."),
            ("Nutrition", "Remember to hydrate and log your meals."),
            ("Maintenance", "Demo equipment maintenance records are available."),
            ("Member progress", "Track measurements to review progress over time."),
        ]
        for index, (title, message) in enumerate(announcements, start=1):
            self._record(
                Announcement,
                {"title": f"[DEMO] {title}"},
                {
                    "message": f"[DEMO] {message}",
                    "audience": User.Role.MEMBER,
                    "created_by": admin_user,
                    "expires_at": timezone.now() + timedelta(days=30 + index),
                },
            )
