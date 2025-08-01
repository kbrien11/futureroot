import logging
from celery import shared_task
from .models import Location
from .utils import enrich_location_with_aarp_scores

logger = logging.getLogger(__name__)


@shared_task
def refresh_missing_zip_scores():
    missing = Location.objects.filter(livability_score__isnull=True)
    logger.info(f"Starting enrichment for {missing.count()} ZIPs")

    for loc in missing:
        try:
            enrich_location_with_aarp_scores(loc, loc.zip_code)
            logger.info(f"Updated ZIP {loc.zip_code}")
        except Exception as e:
            logger.error(f"Error enriching ZIP {loc.zip_code}: {e}")
