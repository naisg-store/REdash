# PropPulse (REdash) - Huntington Beach Realtor Edge Roadmap

This document outlines the phased feature expansions for the PropPulse real estate permit intelligence dashboard. The goal is to keep the frontend clean, fast, and focused purely on high-converting off-market signals in Huntington Beach.

---

## Phase 1: Core Dashboard Foundation (Completed ✅)
- [x] Python Playwright scraper targeting Huntington Beach Accela portal (`hb_scraper.py`).
- [x] Automated daily pipeline via GitHub Actions.
- [x] Modern, dark-mode Tailwind CSS executive UI (`index.html`).
- [x] Live data fetch from `leads.json`.
- [x] Frontend sorting (High-priority ADU/Remodels pushed to top, ordered by recency).
- [x] Category filters, search input, and JSON/CSV export tool.

---

## Phase 2: Enhanced Lead Categorization & Valuation (Next Up 🚧)
- [ ] **Scope Valuation Tagging:** Expand the Python scraper to parse permit descriptions for valuation keywords or square footage so we can categorize leads as *Micro*, *Mid-Scale*, or *Heavy Capital*.
- [ ] **Contractor vs. Owner-Builder Flag:** Automatically identify whether a licensed General Contractor is attached to the permit (signaling a serious flip/investment) vs. an owner-builder (DIY/resident).
- [ ] **Direct Accela Deep-Links:** Ensure every card maps straight to its unique record ID on the municipal portal for instant verification.

---

## Phase 3: Hyper-Local HB Neighborhood Filters (Future 📌)
- [ ] Add a geographic filter dropdown mapping specific HB micro-markets:
  - *Downtown / Main Street (92648)*
  - *Huntington Harbour (92649)*
  - *Goldenwest / West HB (92647)*
  - *Brookhurst / South HB (92646)*

---

## Phase 4: One-Click Agent Outreach Toolkit (Future 📌)
- [ ] Add a collapsible "Outreach Drawer" to each permit card featuring:
  - Pre-written SMS / Mailer templates tailored to the specific permit type (e.g., ADU proposal vs. post-reno market valuation).
  - Quick-copy address formatting for direct mail campaigns.
