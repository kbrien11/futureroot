from django.core.management.base import BaseCommand
from uszipcode import SearchEngine
from uszipcode.search import SearchEngine as ZipSearch
from locations.models import Location


class Command(BaseCommand):
    help = "Backfills Niche school URLs into Location using ZIP → town/state lookup"

    def handle(self, *args, **kwargs):
        search = ZipSearch()
        updated, skipped, failed = 0, 0, 0

        for loc in Location.objects.all():
            zip_code = str(loc.zip_code)
            if not zip_code:
                skipped += 1
                continue

            result = search.by_zipcode(zip_code)

            if not result or not result.major_city or not result.state:
                print(f"⚠️ {zip_code}: Failed to resolve city/state via uszipcode")
                failed += 1
                continue

            town = result.major_city
            state = result.state

            # Generate Niche URL
            slug = town.lower().replace(" ", "-").replace("'", "")
            url = f"https://www.niche.com/k12/search/best-public-schools/m/{slug}-{state.lower()}/"

            # Backfill only if not already set
            if not loc.niche_school_url:
                loc.niche_school_url = url
                loc.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"🏫 Niche school URLs backfilled — Updated: {updated}, Skipped: {skipped}, Failed ZIPs: {failed}"
            )
        )
