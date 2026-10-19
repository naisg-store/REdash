import json
from datetime import datetime, timedelta
import time
from playwright.sync_api import sync_playwright

def scrape_hb_permits():
    portal_url = "https://aca-prod.accela.com/COHB/Cap/CapHome.aspx?module=Building&TabName=Home"
    
    today = datetime.now()
    start_date = (today - timedelta(days=14)).strftime("%m/%d/%Y")
    end_date = today.strftime("%m/%d/%Y")

    print(f"[*] Opening browser to HB Accela Portal ({start_date} to {end_date})...")
    leads = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        
        try:
            page.goto(portal_url, timeout=60000, wait_until="domcontentloaded")

            # 1. Target the inputs in the main document using the exact Huntington Beach IDs
            start_input = page.locator("input[id='ctl00_PlaceHolderMain_generalSearchForm_txtGSStartDate']")
            end_input = page.locator("input[id='ctl00_PlaceHolderMain_generalSearchForm_txtGSEndDate']")

            start_input.wait_for(state="visible", timeout=20000)

            # 2. Inject the dates directly using JavaScript to bypass the Accela input mask
            start_input.evaluate("(element, value) => element.value = value", start_date)
            end_input.evaluate("(element, value) => element.value = value", end_date)
            print("[+] Dates forcefully injected, bypassing input masks.")

            # 3. Click the exact Search button ID
            search_btn = page.locator("a#ctl00_PlaceHolderMain_btnNewSearch")
            search_btn.scroll_into_view_if_needed()
            search_btn.click()
            print("[*] Search submitted. Waiting for results table...")

            # 4. Wait for the permit table to render
            table_selector = "table[id*='gdvPermitList']"
            page.wait_for_selector(table_selector, timeout=25000)

            # 5. Extract rows across all available pages
            page_num = 1
            while True:
                # Give the DOM a brief moment to settle after pagination loads
                page.wait_for_timeout(2000)
                
                rows = page.locator(f"{table_selector} tr.ACA_TabRow_Odd, {table_selector} tr.ACA_TabRow_Even").all()
                print(f"[+] Scraping page {page_num}: Found {len(rows)} records on this view.")

                for row in rows:
                    cols = row.locator("td").all_inner_texts()
                    if len(cols) >= 5:
                        record_num = cols[1].strip()
                        date_filed = cols[2].strip()
                        record_type = cols[3].strip()
                        description = cols[4].strip() if len(cols) > 4 else "Building Permit"
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

                        leads.append({
                            "id": record_num,
                            "date": date_filed,
                            "address": address or "Huntington Beach, CA",
                            "event": record_type,
                            "description": description,
                            "status": "Permit Issued",
                            "action": action
                        })

                # Check for the 'Next >' pagination link using the exact text and class
                next_link = page.locator("a.aca_simple_text", has_text="Next >").first
                
                if next_link.count() > 0 and next_link.is_visible():
                    print(f"[*] Navigating to page {page_num + 1}...")
                    next_link.click()
                    
                    # Wait for the invisible ASP.NET postback to finish downloading the next page
                    page.wait_for_load_state("networkidle")
                    
                    # Add a 3-second buffer for the JavaScript to inject the new rows into the table
                    page.wait_for_timeout(3000)
                    page_num += 1
                else:
                    print("[+] Reached the final page.")
                    break
                    
        except Exception as e:
            print(f"[-] Error encountered: {e}")
            
        finally:
            browser.close()

        if leads:
            with open("leads.json", "w") as f:
                json.dump(leads, f, indent=2)
            print(f"[✓] Saved {len(leads)} total live records to leads.json.")
        else:
            print("[!] No records extracted. Existing leads.json preserved.")

if __name__ == "__main__":
    scrape_hb_permits()