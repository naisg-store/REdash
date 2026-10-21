import json
import os
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def scrape_hb_permits():
    portal_url = "https://aca-prod.accela.com/COHB/Cap/CapHome.aspx?module=Building&TabName=Home"
    
    today = datetime.now()
    start_date = (today - timedelta(days=14)).strftime("%m/%d/%Y")
    end_date = today.strftime("%m/%d/%Y")

    print(f"[*] Opening browser to HB Accela Portal ({start_date} to {end_date})...")
    leads = []
    
    with sync_playwright() as p:
        # Automatically detects if running on GitHub Actions and switches to headless mode
        is_ci = os.getenv("CI") == "true"
        browser = p.chromium.launch(headless=is_ci, slow_mo=100 if not is_ci else 0)
        page = browser.new_page()
        
        try:
            page.goto(portal_url, timeout=60000, wait_until="domcontentloaded")

            start_input = page.locator("input[id='ctl00_PlaceHolderMain_generalSearchForm_txtGSStartDate']")
            end_input = page.locator("input[id='ctl00_PlaceHolderMain_generalSearchForm_txtGSEndDate']")
            start_input.wait_for(state="visible", timeout=20000)

            start_input.evaluate("(element, value) => element.value = value", start_date)
            end_input.evaluate("(element, value) => element.value = value", end_date)
            
            search_btn = page.locator("a#ctl00_PlaceHolderMain_btnNewSearch")
            search_btn.scroll_into_view_if_needed()
            search_btn.click()
            
            table_selector = "table[id*='gdvPermitList']"
            page.wait_for_selector(table_selector, timeout=25000)

            page_num = 1
            while True:
                page.wait_for_timeout(2000)
                rows = page.locator(f"{table_selector} tr.ACA_TabRow_Odd, {table_selector} tr.ACA_TabRow_Even").all()
                
                for row in rows:
                    cols = row.locator("td").all_inner_texts()
                    if len(cols) >= 5:
                        # Correct column mapping: Col 1 = Date, Col 2 = Permit ID
                        date_filed = cols[1].strip()
                        record_num = cols[2].strip()
                        record_type = cols[3].strip()
                        
                        # Preserve clerk markers (***) while normalizing whitespace
                        raw_desc = cols[4].strip() if len(cols) > 4 else "Building Permit"
                        description = re.sub(r'\s+', ' ', raw_desc).strip()

                        address = cols[5].strip() if len(cols) > 5 else "Huntington Beach, CA"

                        desc_lower = description.lower()
                        
                        if "adu" in desc_lower or "accessory dwelling" in desc_lower:
                            action = "ADU Investor Lead"
                        elif "remodel" in desc_lower or "addition" in desc_lower:
                            action = "Major Remodel / Flipper"
                        elif "demolition" in desc_lower:
                            action = "Re-development Prospect"
                        else:
                            action = "General Construction"

                        if "sq ft" in desc_lower or "sqft" in desc_lower or "addition" in desc_lower or "new" in desc_lower:
                            scope = "Heavy Capital"
                        elif "remodel" in desc_lower or "bath" in desc_lower or "kitchen" in desc_lower:
                            scope = "Mid-Scale"
                        else:
                            scope = "Micro / Routine"

                        contractor_status = "Owner/Builder" if "owner" in desc_lower else "GC Attached"

                        zip_match = re.search(r'926\d{2}', address)
                        zip_code = zip_match.group(0) if zip_match else "Unknown"

                        leads.append({
                            "id": record_num,
                            "date": date_filed,
                            "address": address or "Huntington Beach, CA",
                            "zip": zip_code,
                            "event": record_type,
                            "description": description,
                            "status": "Permit Issued",
                            "action": action,
                            "scope": scope,
                            "contractor": contractor_status
                        })

                next_link = page.locator("a.aca_simple_text", has_text="Next >").first
                
                if next_link.count() > 0 and next_link.is_visible():
                    next_link.click()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(3000)
                    page_num += 1
                else:
                    break
                    
        except Exception as e:
            print(f"[-] Error encountered: {e}")
        finally:
            browser.close()

        if leads:
            with open("leads.json", "w") as f:
                json.dump(leads, f, indent=2)
            print(f"[✓] Saved {len(leads)} live records to leads.json.")

if __name__ == "__main__":
    scrape_hb_permits()
