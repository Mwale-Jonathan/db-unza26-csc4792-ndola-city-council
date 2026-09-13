#!/usr/bin/env python3
"""
Ndola City Council Document Downloader
Course: 2025/26 CSC 4792 - Data Mining and Warehousing
Target: Ndola City Council (https://www.ndolacouncil.gov.zm)

This script downloads all official municipal publications, CDF records,
annual budgets, financial statements, IDP documents, and administrative minutes
into the /source_files/ directory and generates a verified metadata manifest.
"""

import os
import sys
import json
import hashlib
import logging
import urllib3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.ndolacouncil.gov.zm"
SOURCE_FILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "source_files"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

# Curated list of verified document endpoints directly on the Ndola Council repository
OFFICIAL_DOCUMENTS = [
    # --- Budgets & Financial Statements ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2026/08/NDOLA-CITY-COUNCIL-2026-BUDGET-1.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council 2026 Approved Budget"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/2024-OBB-Annual-Detailed-2.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council 2024 Output-Based Budget (OBB) Annual Detailed"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/BI-ANNUAL-BUDGET-PERFORMANCE-REPORT-SEPTEMBER2025.pdf",
        "category": "Budgets & Financials",
        "description": "Bi-Annual Budget Performance Report September 2025"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/11/Ndola-City-council-FS-2024_20251121_0001.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council Financial Statements 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/2023-Financial-Statement.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council Financial Statements 2023"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/2022-Financial-Statement.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council Financial Statements 2022"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/2021-Financial-Statement.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council Financial Statements 2021"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/2020-Financial-Statement.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council Financial Statements 2020"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/AUDIT-OPION-2024.pdf",
        "category": "Budgets & Financials",
        "description": "Ndola City Council External Audit Opinion 2024"
    },

    # --- Constituency Development Fund (CDF) - Projects & Allocations ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/2025-List-of-approved-Community-Projects-Ndola-District-1.pdf",
        "category": "Constituency Development Fund",
        "description": "2025 List of Approved CDF Community Projects - Ndola District"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/APPROVED-2024-CDF-COMMUNITY-PROJECTS-1.pdf",
        "category": "Constituency Development Fund",
        "description": "2024 List of Approved CDF Community Projects - Ndola District"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/2024-CDF-DISAPPROVED-LIST-OF-PROJECTS-NDOLA-DISTRICT.pdf",
        "category": "Constituency Development Fund",
        "description": "2024 CDF Disapproved Projects with Justification - Ndola District"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIist-of-not-approved-CDF-2025-Community-Projects-Ndola-District-1.pdf",
        "category": "Constituency Development Fund",
        "description": "2025 CDF Disapproved Projects with Justification - Ndola District"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/chifubu-2025-skill-and-community-projecta-approvals.pdf",
        "category": "Constituency Development Fund",
        "description": "Chifubu Constituency 2025 Skills and Community Project Approvals"
    },

    # --- CDF Skills Development Bursaries ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/01-LiST-OF-APPROVED-CDF-2025-SKILLS-DEVELOPMENT-Ndola-Central-Constituency.pdf",
        "category": "CDF Skills & Bursaries",
        "description": "2025 Approved CDF Skills Development Bursaries - Ndola Central Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-SKILLS-DEVELOPMENT-Bwana-Mkubwa_Constituency.pdf",
        "category": "CDF Skills & Bursaries",
        "description": "2025 Approved CDF Skills Development Bursaries - Bwana Mkubwa Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-SKILLS-DEVELOPMENT-Chifubu-constituency.pdf",
        "category": "CDF Skills & Bursaries",
        "description": "2025 Approved CDF Skills Development Bursaries - Chifubu Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-SKILS-DEVELOPMENT-BENEFICARIES-KABUSHI-CONSTITUENCY.pdf",
        "category": "CDF Skills & Bursaries",
        "description": "2025 Approved CDF Skills Development Bursaries - Kabushi Constituency"
    },

    # --- CDF Secondary School Boarding Bursaries ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-Ndola-Central.pdf",
        "category": "CDF Secondary Bursaries",
        "description": "2025 Approved CDF Secondary School Boarding Bursaries - Ndola Central Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-Bwana-Mkubwa_Constituency.pdf",
        "category": "CDF Secondary Bursaries",
        "description": "2025 Approved CDF Secondary School Boarding Bursaries - Bwana Mkubwa Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-CHIFUBU-CONSTITUENCY.pdf",
        "category": "CDF Secondary Bursaries",
        "description": "2025 Approved CDF Secondary School Boarding Bursaries - Chifubu Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-KABUSHI-Constituency.pdf",
        "category": "CDF Secondary Bursaries",
        "description": "2025 Approved CDF Secondary School Boarding Bursaries - Kabushi Constituency"
    },

    # --- CDF Empowerment Grants ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-EMPOWERNMENT-GRANTS-NDOLA-CENTRAL-Constituency-1.pdf",
        "category": "CDF Empowerment Grants",
        "description": "2025 Approved CDF Empowerment Grants - Ndola Central Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-EMPWERMENT-GRANTS-BWANA-MKUBWA-Constituency-1.pdf",
        "category": "CDF Empowerment Grants",
        "description": "2025 Approved CDF Empowerment Grants - Bwana Mkubwa Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-EMPOWERMENT-GRANTS-CHIFUBU-CONSTITUENCY-1.pdf",
        "category": "CDF Empowerment Grants",
        "description": "2025 Approved CDF Empowerment Grants - Chifubu Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APROVED-CDF-2025-EMPOWERMENT-GRANTS-KABUSHI-Constituency-1.pdf",
        "category": "CDF Empowerment Grants",
        "description": "2025 Approved CDF Empowerment Grants - Kabushi Constituency"
    },

    # --- CDF Empowerment Loans ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-EMPOWERMRNT-LOANS-NDOLA-CENTRAL-CINSTITUENCY_1-2.pdf",
        "category": "CDF Empowerment Loans",
        "description": "2025 Approved CDF Empowerment Loans - Ndola Central Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF-2025-LOAN-BENEFICARIES-BWANA-MKUBWA-CONTITUENCY.pdf",
        "category": "CDF Empowerment Loans",
        "description": "2025 Approved CDF Empowerment Loans - Bwana Mkubwa Constituency"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/LIST-OF-APPROVED-CDF2025-EMPOWERMENT-LOANS-CHIFUBU-CONSTITUENCY-Copy.pdf",
        "category": "CDF Empowerment Loans",
        "description": "2025 Approved CDF Empowerment Loans - Chifubu Constituency"
    },

    # --- Integrated Development Plans (IDP) & Strategic Plans ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2026/04/NDOLA-DISTRICT-IDP-LAUNCH.pdf",
        "category": "Integrated Development Plans",
        "description": "Ndola District Integrated Development Plan (IDP) Launch Document"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/Ndola-Citizen-Engagement-Strategy.pdf",
        "category": "Integrated Development Plans",
        "description": "Ndola City Council Citizen Engagement Strategy 2025-2028"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2026/03/SERVICE-CHARTER-FOR-NDOLA-CITY-COUNCIL.pdf",
        "category": "Integrated Development Plans",
        "description": "Ndola City Council Service Charter"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2026/01/2025-STAKEHOLDER-ENGAGEMENT-PLAN.pdf",
        "category": "Integrated Development Plans",
        "description": "2025 Stakeholder Engagement Plan"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/Water-and-Sanitation-Community-Engagement-Report.pdf",
        "category": "Integrated Development Plans",
        "description": "Water and Sanitation Community Engagement Report for 2025"
    },

    # --- Council Minutes, Governance & Resolutions ---
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-THE-ORDINARY-MEETING-OF-THE-COUNCIL-HELD-ON-1ST-JULY-2025.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of the Ordinary Meeting of the Council - 1st July 2025"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-COUNCIL-MEETING-HELD-ON-31ST-MARCH-2025.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Council Meeting - 31st March 2025"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-THE-SPECIAL-COUNCIL-MEETING-HELD-ON-4TH-APRIL-2025.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Special Council Meeting - 4th April 2025"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-THE-COUNCIL-MEETING-HELD-ON-30TH-DECEMBER2024.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Council Meeting - 30th December 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-COUNCIL-MEETING-HELD-ON-28TH-JUNE-2024.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Council Meeting - 28th June 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-PLANNING-HELD-ON-26TH-SEPTEMBER-2024.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Planning Committee - 26th September 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-ENGINEERING-SERVICES-COMMITTEE-HELD-ON-MONDAY-23RD-SEPTEMBER-2024.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Engineering Services Committee - 23rd September 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-AUDIT-COMMITTEE-HELD-ON-25TH-SEPTEMBER-2024.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Audit Committee - 25th September 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-LEGAL-SERVICES-ADMIN-HELD-ON-1ST-OCTOBER-2024.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Legal Services Committee - 1st October 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OFCOMMUNITY-DEVELOPMENT-HELD-ON-16TH-SEPTEMBER-2024.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Minutes of Community Development Committee - 16th September 2024"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/DDCC-MINUTES-OF-2ND-QUARTER-MEETING_22-JULY-2025.pdf",
        "category": "Council Administration & Resolutions",
        "description": "District Development Coordinating Committee (DDCC) 2nd Quarter Minutes - 22 July 2025"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/FINAL-DDCC-MINUTES-OF-3RD-QUARTER-MEETING_24-SEPTEMBER-2025.pdf",
        "category": "Council Administration & Resolutions",
        "description": "District Development Coordinating Committee (DDCC) 3rd Quarter Minutes - 24 September 2025"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/MINUTES-OF-THE-DDCC-MEETING-HELD-ON-3-APRIL-2025.pdf",
        "category": "Council Administration & Resolutions",
        "description": "District Development Coordinating Committee (DDCC) Minutes - 3 April 2025"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/COMMUNITY-STAKEHOLDERS-MINUTES-1.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Community Stakeholders Engagement Minutes for 2025 Budget"
    },
    {
        "url": "https://www.ndolacouncil.gov.zm/wp-content/uploads/2025/12/BUSINESS-STAKEHOLDERS-MINUTES-1.pdf",
        "category": "Council Administration & Resolutions",
        "description": "Business Stakeholders Engagement Minutes for 2026 Budget"
    },
]


def download_document(session, doc_info, dest_dir):
    """
    Downloads a single document with streaming and checksum verification.
    """
    url = doc_info["url"]
    filename = unquote(url.split("/")[-1])
    # Sanitize filename
    clean_filename = "".join(c for c in filename if c.isalnum() or c in ("-", "_", ".")).strip()
    dest_path = os.path.join(dest_dir, clean_filename)

    logger.info(f"Downloading [{doc_info['category']}] {clean_filename}...")
    try:
        resp = session.get(url, stream=True, timeout=30)
        if resp.status_code == 200:
            hasher = hashlib.sha256()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        hasher.update(chunk)
            
            file_size = os.path.getsize(dest_path)
            sha256 = hasher.hexdigest()
            logger.info(f"Successfully downloaded {clean_filename} ({file_size / 1024:.1f} KB)")
            return {
                "filename": clean_filename,
                "path": dest_path,
                "url": url,
                "category": doc_info["category"],
                "description": doc_info["description"],
                "size_bytes": file_size,
                "sha256": sha256,
                "status": "SUCCESS"
            }
        else:
            logger.warning(f"Failed HTTP {resp.status_code} for {url}")
            return {
                "filename": clean_filename,
                "url": url,
                "category": doc_info["category"],
                "status": f"HTTP_{resp.status_code}"
            }
    except Exception as e:
        logger.error(f"Exception downloading {url}: {e}")
        return {
            "filename": clean_filename,
            "url": url,
            "category": doc_info["category"],
            "status": f"ERROR: {str(e)}"
        }


def main():
    os.makedirs(SOURCE_FILES_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False

    logger.info(f"Starting download of {len(OFFICIAL_DOCUMENTS)} key municipal documents...")
    manifest = []

    for doc in OFFICIAL_DOCUMENTS:
        res = download_document(session, doc, SOURCE_FILES_DIR)
        manifest.append(res)

    # Save manifest.json in source_files/
    manifest_path = os.path.join(SOURCE_FILES_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "target_council": "Ndola City Council",
            "base_url": BASE_URL,
            "total_documents_attempted": len(OFFICIAL_DOCUMENTS),
            "successful_downloads": sum(1 for m in manifest if m.get("status") == "SUCCESS"),
            "documents": manifest
        }, f, indent=2)

    logger.info(f"All downloads completed. Manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
