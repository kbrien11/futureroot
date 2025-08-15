import os
from uszipcode import SearchEngine

import pandas as pd
from locations.models import Location
from decouple import config
import requests
from playwright.sync_api import sync_playwright
from math import radians, sin, cos, sqrt, atan2


RENTCAST_API_KEY = config("RENTCAST_API_KEY")  # <- Add your actual key here


def enrich_locations_with_ndcp(ndcp_path: str, zip_county_path: str) -> dict:
    """
    Loads NDCP infant cost data (county-level) and ZIP-county mapping,
    then populates Location model with zip_code, county_fips, and infant care cost.
    Returns: dict of {zip_code: weekly_cost}
    """
    if not os.path.exists(ndcp_path):
        raise ValueError(f"NDCP file not found: {ndcp_path}")
    if not os.path.exists(zip_county_path):
        raise ValueError(f"ZIP–county file not found: {zip_county_path}")

    # 👉 Load NDCP file
    ndcp_df = pd.read_excel(ndcp_path, engine="openpyxl")

    ndcp_df.columns = ndcp_df.columns.str.upper().str.strip()
    ndcp_df["COUNTY_FIPS_CODE"] = ndcp_df["COUNTY_FIPS_CODE"].astype(str).str.zfill(5)
    ndcp_df["MCINFANT"] = pd.to_numeric(ndcp_df["MCINFANT"], errors="coerce")
    ndcp_df = ndcp_df.dropna(subset=["COUNTY_FIPS_CODE", "MCINFANT"])

    # 👉 Load ZIP-to-county file
    zip_df = pd.read_excel(zip_county_path, engine="openpyxl")
    print(zip_df.columns.tolist())

    zip_df.columns = zip_df.columns.str.upper().str.strip()
    zip_df["ZIP"] = zip_df["ZIP"].astype(str).str.zfill(5)
    zip_df["COUNTY"] = zip_df["COUNTY"].astype(str).str.zfill(5)

    # 🔗 Merge ZIPs with NDCP cost using county FIPS
    merged = zip_df.merge(
        ndcp_df[["COUNTY_FIPS_CODE", "MCINFANT"]],
        left_on="COUNTY",
        right_on="COUNTY_FIPS_CODE",
        how="inner",
    ).drop_duplicates(subset=["ZIP"])

    # 🚀 Populate Location table
    inserted, updated = 0, 0
    cost_map = {}

    for _, row in merged.iterrows():
        zip_code = row["ZIP"]
        cost = row["MCINFANT"]

        loc, was_created = Location.objects.update_or_create(
            zip_code=zip_code,
            defaults={"cost_center_infant": cost},
        )
        cost_map[zip_code] = cost
        if was_created:
            inserted += 1
        else:
            updated += 1

    print(f"✅ Locations enriched: {inserted} created, {updated} updated")
    return cost_map


def get_rentcast_data(zip_code: str) -> dict:
    """
    Fetches housing market data from RentCast API for the given ZIP code.
    Returns: dict with median rent, home price, rent-to-price ratio, etc.
    """

    url = "https://api.rentcast.io/v1/properties"
    headers = {"X-Api-Key": RENTCAST_API_KEY, "Accept": "application/json"}
    params = {"zipcode": zip_code}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "zip_code": zip_code,
            "median_rent": data.get("medianRent"),
            "median_price": data.get("medianHomePrice"),
            "rent_price_ratio": data.get("rentPriceRatio"),
            "timestamp": data.get("lastUpdated"),
        }

    except requests.RequestException as e:
        print(f"RentCast API error for {zip_code}: {e}")
        return {}


def scrape_aarp_scores(zip_code):
    from playwright.sync_api import sync_playwright

    categories = [
        "Overall",
        "Housing",
        "Neighborhood",
        "Transportation",
        "Environment",
        "Health",
        "Engagement",
        "Opportunity",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            url = f"https://livabilityindex.aarp.org/search/{zip_code}%2C%20United%20States"
            page.goto(url, timeout=15000)
            page.wait_for_selector("svg text", timeout=10000)

            locator = page.locator("li", has_text="Median Household Income:")
            value = locator.evaluate(
                "node => node.textContent.replace('Median Household Income:', '').trim()"
            )

            # Grab all SVG <text> nodes
            text_nodes = page.query_selector_all("svg text")
            raw_text = [node.text_content().strip() for node in text_nodes]

            # Filter numeric values only
            numbers = [val for val in raw_text if val.isdigit()]

            # Extract scores using the repeating pattern: every 3rd item starting at index 5
            scores = [int(numbers[i]) for i in range(5, len(numbers), 3)]

            # Trim to number of known categories
            scores = scores[: len(categories)]

            score_dict = dict(zip(categories, scores))
            score_dict["Income"] = value

            browser.close()
            return score_dict

        except Exception as e:
            print(f"Error scraping AARP scores for ZIP {zip_code}: {e}")
            browser.close()
            return {}


def assign_livability_grade(score):
    """
    Assigns a letter grade based on livability score (0–100 scale).
    """
    try:
        score = int(float(score))  # handles numeric strings like "72.0"
    except (ValueError, TypeError):
        return None  # gracefully bail on non-numeric inputs
    if score >= 75:
        return "A+"
    elif score >= 65:
        return "A"
    elif score >= 57:
        return "B-"
    elif score >= 47:
        return "C+"
    elif score >= 40:
        return "C"
    elif score >= 35:
        return "C-"
    elif score >= 25:
        return "D"
    else:
        return "F"


def enrich_location_with_aarp_scores(loc, zip_code):
    """
    Scrapes AARP scores for a ZIP and updates the Location model instance.
    """
    score = scrape_aarp_scores(zip_code)
    print(zip_code)
    print(score)

    loc.livability_score = assign_livability_grade(score.get("Overall"))
    loc.housing_score = assign_livability_grade(score.get("Housing"))
    loc.neighborhood_score = assign_livability_grade(score.get("Neighborhood"))
    loc.transportation_score = assign_livability_grade(score.get("Transportation"))
    loc.environment_score = assign_livability_grade(score.get("Environment"))
    loc.health_score = assign_livability_grade(score.get("Health"))
    loc.engagement_score = assign_livability_grade(score.get("Engagement"))
    loc.opportunity_score = assign_livability_grade(score.get("Opportunity"))
    loc.median_household_income = score.get("Income")

    loc.save()


def haversine(lat1, lon1, lat2, lon2):

    R = 3959  # Earth radius in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def get_coords(zip_code):
    search = SearchEngine()
    result = search.by_zipcode(zip_code)
    return result.lat, result.lng
