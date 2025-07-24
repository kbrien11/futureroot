from django.core.management.base import BaseCommand
from uszipcode.search import SearchEngine as ZipSearch
from locations.models import Location


class Command(BaseCommand):
    help = "Backfills GreatSchools ZIP search URLs into Location using ZIP → city/state lookup"

    def handle(self, *args, **kwargs):
        search = ZipSearch()
        updated, skipped, failed = 0, 0, 0

        for loc in Location.objects.all():
            if not loc.housing_cost:
                skipped += 1
                continue

            # Generate GreatSchools ZIP search URL
            url = f"https://www.greatschools.org/search/search.page?search_type=school&q={loc.zip_code}"

            # Backfill only if not already set

            loc.great_schools_url = url
            loc.save()
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"📚 GreatSchools URLs backfilled — Updated: {updated}, Skipped: {skipped}, Failed ZIPs: {failed}"
            )
        )
