from playwright.sync_api import sync_playwright
import time
import random


def test_greatschools_zip(zip_code="07006"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        url = f"https://www.greatschools.org/search/search.page?search_type=school&q={zip_code}"
        print(f"🔍 Visiting: {url}")
        page.goto(url, timeout=15000)
        page.wait_for_timeout(random.randint(2500, 4000))

        # Updated selectors
        school_cards = page.locator("div.search-result-card")
        count = school_cards.count()
        print(f"🏫 Found {count} school cards for ZIP {zip_code}")

        scores = []
        for i in range(count):
            rating_el = school_cards.nth(i).locator("span.gs-rating-number")
            if rating_el.is_visible():
                rating_text = rating_el.inner_text().strip()
                try:
                    score = float(rating_text)
                    scores.append(score)
                    print(f"✅ School #{i+1}: Rating = {score}")
                except ValueError:
                    print(f"⚠️ School #{i+1}: Unreadable rating")

        if scores:
            avg = round(sum(scores) / len(scores), 2)
            print(f"\n📊 ZIP {zip_code} — Avg rating: {avg}")
        else:
            print(f"\n⚠️ No ratings found for ZIP {zip_code}")

        browser.close()


if __name__ == "__main__":
    test_greatschools_zip()
