from django.core.management.base import BaseCommand
from childcare.models import Childcare


class Command(BaseCommand):
    help = "Extract and update town field for all Childcare entries"

    def handle(self, *args, **kwargs):
        updated, skipped, already_set = 0, 0, 0

        for c in Childcare.objects.all():
            # Skip if town is already set
            if c.town and str(c.town).strip():
                already_set += 1
                continue

            town = c.extract_town()
            if town:
                c.town = town
                c.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Town backfill complete — Updated: {updated}, Skipped: {skipped}, Already set: {already_set}"
            )
        )
