import os
import pandas as pd
from locations.models import Location
from decouple import config
import requests

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
