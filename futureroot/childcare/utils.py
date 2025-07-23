import re
from childcare.models import Childcare


def estimate_cost_per_month(
    median_income: float, base_cost: float = 1200.0, baseline_income: float = 70000.0
):
    if median_income is None or median_income == 0:
        return base_cost  # fallback to national average
    multiplier = median_income / baseline_income
    return round(base_cost * multiplier, 2)


def extract_zip(address: str) -> str | None:
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


def get_unique_zip_codes():
    zip_set = set()
    for provider in Childcare.objects.all():
        zip_code = extract_zip(provider.address)
        if zip_code:
            zip_set.add(zip_code)
    return list(zip_set)


def get_zip_from_address(address):
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


def formatted_cost(value):
    return "${:,.0f}".format(value)
