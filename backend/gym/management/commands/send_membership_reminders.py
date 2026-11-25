from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from gym.models import Membership, Notification


class Command(BaseCommand):
    help = "Create in-app reminders for memberships expiring within seven days."

    def handle(self, *args, **options):
        today = timezone.localdate()
        unfrozen = Membership.objects.filter(
            status=Membership.Status.FROZEN, frozen_until__lte=today
        ).update(status=Membership.Status.ACTIVE, frozen_until=None)
        expired = Membership.objects.filter(
            status=Membership.Status.ACTIVE, end_date__lt=today
        ).update(status=Membership.Status.EXPIRED)
        memberships = Membership.objects.select_related("member__user").filter(
            status=Membership.Status.ACTIVE,
            end_date__range=(today, today + timedelta(days=7)),
        )
        created = 0
        for membership in memberships:
            title = "Membership expiring soon"
            if not Notification.objects.filter(
                recipient=membership.member.user,
                title=title,
                message__contains=f"membership #{membership.pk}",
                created_at__date=today,
            ).exists():
                Notification.objects.create(
                    recipient=membership.member.user,
                    title=title,
                    message=f"Your {membership.package.name} membership #{membership.pk} expires on {membership.end_date}.",
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"Created {created} reminder(s), expired {expired} membership(s), and unfroze {unfrozen}."
        ))
