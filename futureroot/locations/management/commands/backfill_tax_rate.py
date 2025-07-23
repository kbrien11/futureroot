import os
import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from locations.models import Location

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IRS_DATA_PATH = os.path.join(BASE_DIR, "data", "irsData.csv")
B25077_DATA_PATH = os.path.join(BASE_DIR, "data", "B25077_median_home_value.csv")
B25103_DATA_PATH = os.path.join(BASE_DIR, "data", "B25103_property_taxes_paid.csv")


class Command(BaseCommand):
    help = "Calculates effective property tax rate using Census B25077 + B25103"

    def handle(self, *args, **kwargs):
        try:
            home_df = pd.read_csv(B25077_DATA_PATH)
            tax_df = pd.read_csv(B25103_DATA_PATH)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error loading CSVs: {e}"))
            return

        # 🎯 Extract ZIP codes
        home_df["zip_code"] = home_df["NAME"].str.extract(r"ZCTA5 (\d{5})")
        tax_df["zip_code"] = tax_df["NAME"].str.extract(r"ZCTA5 (\d{5})")

        # ✅ Clean and coerce home value
        home_df["B25077I_001E"] = pd.to_numeric(
            home_df["B25077I_001E"], errors="coerce"
        ).fillna(0)
        home_df["median_home_value"] = home_df["B25077I_001E"]  # assuming full dollars

        # ✅ Clean total households column from strings like "10,000+"
        if "B25103_001E" in tax_df.columns:
            tax_df["B25103_001E"] = (
                tax_df["B25103_001E"]
                .astype(str)
                .str.replace("+", "", regex=False)
                .str.replace(",", "", regex=False)
            )
            tax_df["B25103_001E"] = pd.to_numeric(
                tax_df["B25103_001E"], errors="coerce"
            ).fillna(0)

        # 🧾 Tax bracket midpoints
        base_brackets = {
            "B25103_002E": 300,
            "B25103_003E": 800,
            "B25103_004E": 1250,
            "B25103_005E": 1750,
            "B25103_006E": 2250,
            "B25103_007E": 2750,
            "B25103_008E": 3250,
            "B25103_009E": 3750,
            "B25103_010E": 4250,
            "B25103_011E": 15000,  # updated for high-tax ZIPs
        }

        bracket_midpoints = {
            col: mp for col, mp in base_brackets.items() if col in tax_df.columns
        }

        # ✅ Coerce bracket columns
        for col in bracket_midpoints:
            tax_df[col] = pd.to_numeric(tax_df[col], errors="coerce").fillna(0)

        updated, skipped = 0, 0

        for _, tax_row in tax_df.iterrows():
            zip_code = tax_row["zip_code"]
            if pd.isna(zip_code):
                skipped += 1
                continue

            loc = Location.objects.filter(zip_code=zip_code).first()
            home_row = home_df[home_df["zip_code"] == zip_code]
            if not loc or home_row.empty:
                skipped += 1
                continue

            try:
                # ✅ Use DB home_value if present, fallback to Census
                try:
                    home_value = float(loc.home_value)
                    if not home_value:
                        raise ValueError
                except:
                    home_value = float(home_row["median_home_value"].values[0])

                if home_value == 0:
                    raise ValueError("Missing home value")

                total_paid, total_households = 0, 0
                for col, midpoint in bracket_midpoints.items():
                    count = tax_row[col]
                    total_paid += count * midpoint
                    total_households += count

                # 🔧 Optional fallback: use B25103_001E if bracket sum is empty
                if (
                    total_households == 0
                    and "B25103_001E" in tax_row
                    and tax_row["B25103_001E"] > 0
                ):
                    total_households = tax_row["B25103_001E"]
                    avg_tax_paid = 18000  # hardcoded fallback for high-income ZIP
                    tax_rate = (avg_tax_paid / home_value) * 100
                    print(
                        f"⚡ Fallback used for {zip_code}: households={total_households}"
                    )
                elif total_households == 0:
                    raise ValueError("No households reporting")
                else:
                    avg_tax_paid = total_paid / total_households
                    tax_rate = (avg_tax_paid / home_value) * 100

                loc.tax_rate = round(Decimal(tax_rate), 2)
                loc.save()
                updated += 1

                print(
                    f"✅ {zip_code} → avg_tax=${avg_tax_paid:.0f}, home=${home_value:,.0f}, rate={tax_rate:.2f}%"
                )

            except Exception as err:
                print(f"⚠️ {zip_code}: Skipped due to error — {err}")
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"📊 Tax rate backfill complete — Updated: {updated}, Skipped: {skipped}"
            )
        )
