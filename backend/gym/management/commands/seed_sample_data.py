from getpass import getpass
from datetime import timedelta

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from gym.models import (
    Equipment, GymClass, MealPlan, Member, Membership, Package, Payment,
    Staff, User, WorkoutPlan,
)


class Command(BaseCommand):
    help = "Create optional local sample records and set their shared temporary password."

    def handle(self, *args, **options):
        password = getpass("Temporary password for sample accounts: ")
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError(str(error)) from error

        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            raise CommandError("Create a Django superuser first with `python manage.py createsuperuser`.")

        trainer_user, _ = User.objects.get_or_create(
            username="sample.trainer",
            defaults={
                "email": "trainer@example.invalid", "first_name": "Jordan",
                "last_name": "Lee", "role": User.Role.TRAINER,
            },
        )
        trainer_user.role = User.Role.TRAINER
        trainer_user.set_password(password)
        trainer_user.save()
        trainer, _ = Staff.objects.get_or_create(
            user=trainer_user,
            defaults={"title": "Personal trainer", "specialties": "Strength, mobility"},
        )

        package, _ = Package.objects.get_or_create(
            name="Sample 30-day membership",
            defaults={"duration_days": 30, "price": "49.00", "description": "Optional local sample package"},
        )
        members = []
        for username, first, last in [
            ("sample.member1", "Avery", "Morgan"),
            ("sample.member2", "Taylor", "Rivers"),
            ("sample.member3", "Casey", "Jordan"),
        ]:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username.replace('.', '')}@example.invalid",
                    "first_name": first, "last_name": last, "role": User.Role.MEMBER,
                },
            )
            user.role = User.Role.MEMBER
            user.set_password(password)
            user.save()
            member, _ = Member.objects.get_or_create(user=user, defaults={"phone": "555-0100"})
            members.append(member)

        today = timezone.localdate()
        for index, member in enumerate(members):
            membership, created = Membership.objects.get_or_create(
                member=member,
                package=package,
                start_date=today,
                defaults={"end_date": today + timedelta(days=30)},
            )
            if created:
                Payment.objects.create(member=member, membership=membership, amount=package.price, method="card")
            WorkoutPlan.objects.get_or_create(
                member=member, name="Sample strength foundation",
                defaults={
                    "trainer": trainer, "details": [
                        {"exercise": "Goblet squat", "sets": 3, "reps": 10, "weight_kg": 12},
                        {"exercise": "Dumbbell row", "sets": 3, "reps": 10, "weight_kg": 8},
                    ],
                },
            )
            MealPlan.objects.get_or_create(
                member=member, name="Sample balanced day",
                defaults={
                    "trainer": trainer, "daily_calories": 2100, "protein_g": 130,
                    "carbs_g": 230, "fats_g": 65,
                    "meals": [{"name": "Breakfast", "items": ["Oats", "Greek yogurt", "Berries"]}],
                },
            )

        GymClass.objects.get_or_create(
            name="Sample strength circuit",
            defaults={
                "starts_at": timezone.now() + timedelta(days=1),
                "ends_at": timezone.now() + timedelta(days=1, hours=1),
                "trainer": trainer, "capacity": 12, "location": "Studio A",
            },
        )
        Equipment.objects.get_or_create(
            inventory_code="SAMPLE-RACK-01",
            defaults={"name": "Sample squat rack", "quantity": 1, "status": "operational"},
        )
        self.stdout.write(self.style.SUCCESS(
            "Sample records created. Sign in with sample.trainer or sample.member1 and the password you entered."
        ))
