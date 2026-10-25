import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime, timedelta

async def scrape_newport():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 1. Force full desktop viewport so EnerGov renders the full layout
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        all_leads = []
        categories = ["Permit", "Plan"]
        start_date = (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y")

        for category in categories:
            print(f"\n--- Starting category: {category} ---")
            
            # Fresh navigation per category to ensure clean Angular state
            await page.goto("https://css.newportbeachca.gov/EnerGov_Prod/SelfService#/search")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)

            # 2. Select Category
            dropdown = page.locator("#SearchModule")
            await dropdown.wait_for(state="visible", timeout=20000)
            await dropdown.select_option(label=category)
            await page.wait_for_timeout(2000)

            # 3. Open Advanced Search
            # Target the button or link specifically and force click if needed
            advanced_btn = page.locator("a:has-text('Advanced'), button:has-text('Advanced')").first
            await advanced_btn.wait_for(state="visible", timeout=15000)
            await advanced_btn.click()
            await page.wait_for_timeout(2000)

            # 4. Fill Applied Date (matches either #ApplyDateFrom or #PermitCriteria_ApplyDateFrom)
            date_input = page.locator("#ApplyDateFrom, input[id*='ApplyDateFrom']").first
            await date_input.wait_for(state="visible", timeout=20000)
            await date_input.fill(start_date)
            await page.wait_for_timeout(1000)

            # 5. Execute Search
            search_btn = page.locator("button:has-text('Search'), input[value='Search']").first
            await search_btn.click()

            # Wait for pagination dropdown and adjust to 100 per page
            page_size = page.locator("#pageSizeList")
            try:
                await page_size.wait_for(state="visible", timeout=30000)
            except Exception:
                print(f"No results or pagination found for category: {category}")
                continue

            await page_size.select_option(value="100")
            print("Set view to 100 results per page. Waiting for render...")
            await page.wait_for_timeout(6000)

            # 6. Multi-Page Scraping Loop
            page_num = 1
            while True:
                print(f"Scraping {category} - page {page_num}...")

                try:
                    await page.locator('div[id^="entityRecordDiv"]').first.wait_for(state="visible", timeout=20000)
                except Exception:
                    print(f"No more records rendered on page {page_num}.")
                    break

                records = await page.locator('div[id^="entityRecordDiv"]').all()
                print(f"Found {len(records)} records on page {page_num}.")

                for record in records:
                    async def get_val(field_name):
                        loc = record.locator(f'div[name="{field_name}"] span.margin-md-left').first
                        return (await loc.inner_text()).strip() if await loc.count() > 0 else ""

                    record_num = await get_val("label-CaseNumber")
                    if record_num:
                        lead = {
                            "City": "Newport Beach",
                            "Category": category,
                            "Record_Number": record_num,
                            "Applied_Date": await get_val("label-ApplyDate"),
                            "Status": await get_val("label-Status"),
                            "Address": await get_val("label-Address"),
                            "Description": await get_val("label-Description")
                        }
                        all_leads.append(lead)

                # Pagination: Check next link
                next_btn = page.locator("#link-NextPage")
                if await next_btn.count() == 0 or not await next_btn.is_visible():
                    print(f"Reached final page for {category}.")
                    break

                parent_li = page.locator("li:has(#link-NextPage)")
                if await parent_li.count() > 0:
                    class_attr = await parent_li.get_attribute("class") or ""
                    if "disabled" in class_attr:
                        print(f"Reached final page for {category} (next link disabled).")
                        break

                print("Clicking Next Page...")
                await next_btn.click()
                page_num += 1
                await page.wait_for_timeout(5000)

        # 7. Output Combined Leads
        with open("nb_leads.json", "w") as f:
            json.dump(all_leads, f, indent=4)

        print(f"\nFinished! Scraped {len(all_leads)} total records across Permit and Plan.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_newport())
