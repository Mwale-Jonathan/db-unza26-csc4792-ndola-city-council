#!/usr/bin/env python3
"""
Ndola City Council Data Extraction, Cleaning, and Standardization Pipeline
Course: 2025/26 CSC 4792 - Data Mining and Warehousing
Strict Output Rules:
  - Format: CSV
  - Separator: Pipe character '|'
  - Naming Convention: db-unza26-csc4792-[DESCRIPTION].csv
"""

import os
import re
import glob
import json
import logging
import pdfplumber
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_DIR = os.path.join(BASE_DIR, "source_files")
TABULAR_DIR = os.path.join(BASE_DIR, "tabular")


def clean_amount(val):
    if not val or pd.isna(val):
        return 0.0
    val_str = str(val).replace("ZMW", "").replace("K", "").replace(",", "").strip()
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0


def clean_text(text):
    if not text or pd.isna(text):
        return ""
    # Normalize whitespaces and remove pipe characters to preserve CSV delimiter integrity
    cleaned = re.sub(r"\s+", " ", str(text)).replace("|", "/").strip()
    return cleaned


def extract_cdf_community_projects():
    """
    Extracts, merges, and standardizes approved & disapproved CDF community projects for 2024 and 2025.
    """
    logger.info("Extracting CDF Community Projects...")
    records = []

    # 1. 2025 Approved Community Projects
    path_2025_app = os.path.join(SOURCE_DIR, "2025-List-of-approved-Community-Projects-Ndola-District-1.pdf")
    if os.path.exists(path_2025_app):
        with pdfplumber.open(path_2025_app) as pdf:
            for page in pdf.pages:
                for tbl in page.extract_tables():
                    for row in tbl:
                        row_c = [clean_text(c) for c in row]
                        if len(row_c) >= 10 and re.match(r"^\d+$", row_c[0]):
                            records.append({
                                "project_name": row_c[1],
                                "project_description": row_c[2],
                                "sector": row_c[3],
                                "project_type": row_c[4],
                                "constituency": row_c[5],
                                "ward": row_c[6],
                                "zone": row_c[7],
                                "location": row_c[8],
                                "amount_allocated_zmw": clean_amount(row_c[9]),
                                "approval_status": "APPROVED",
                                "fiscal_year": 2025,
                                "justification_notes": row_c[10] if len(row_c) > 10 else "Approved by Ministry/Council"
                            })

    # 2. 2024 Approved Community Projects
    path_2024_app = os.path.join(SOURCE_DIR, "APPROVED-2024-CDF-COMMUNITY-PROJECTS-1.pdf")
    if os.path.exists(path_2024_app):
        with pdfplumber.open(path_2024_app) as pdf:
            for page in pdf.pages:
                for tbl in page.extract_tables():
                    for row in tbl:
                        row_c = [clean_text(c) for c in row]
                        if len(row_c) >= 9 and re.match(r"^\d+$", row_c[0]):
                            records.append({
                                "project_name": row_c[1],
                                "project_description": row_c[2],
                                "sector": row_c[3],
                                "project_type": row_c[4],
                                "constituency": row_c[5],
                                "ward": row_c[6],
                                "zone": row_c[7],
                                "location": row_c[6],  # default to ward
                                "amount_allocated_zmw": clean_amount(row_c[8]),
                                "approval_status": "APPROVED",
                                "fiscal_year": 2024,
                                "justification_notes": row_c[9] if len(row_c) > 9 else "Approved 2024"
                            })

    # 3. 2025 Disapproved Community Projects
    path_2025_dis = os.path.join(SOURCE_DIR, "LIist-of-not-approved-CDF-2025-Community-Projects-Ndola-District-1.pdf")
    if os.path.exists(path_2025_dis):
        with pdfplumber.open(path_2025_dis) as pdf:
            for page in pdf.pages:
                for tbl in page.extract_tables():
                    for row in tbl:
                        row_c = [clean_text(c) for c in row]
                        # Disapproved table has 12 columns
                        if len(row_c) >= 11:
                            sn = row_c[1] if row_c[0] == "" else row_c[0]
                            if re.match(r"^\d+$", sn):
                                offset = 1 if row_c[0] == "" else 0
                                records.append({
                                    "project_name": row_c[offset + 1],
                                    "project_description": row_c[offset + 2],
                                    "sector": row_c[offset + 3],
                                    "project_type": row_c[offset + 4],
                                    "constituency": row_c[offset + 5],
                                    "ward": row_c[offset + 6],
                                    "zone": row_c[offset + 7],
                                    "location": row_c[offset + 8],
                                    "amount_allocated_zmw": 0.0,
                                    "approval_status": "DISAPPROVED",
                                    "fiscal_year": 2025,
                                    "justification_notes": row_c[offset + 10] if len(row_c) > (offset + 10) else row_c[offset + 9]
                                })

    # 4. 2024 Disapproved Community Projects
    path_2024_dis = os.path.join(SOURCE_DIR, "2024-CDF-DISAPPROVED-LIST-OF-PROJECTS-NDOLA-DISTRICT.pdf")
    if os.path.exists(path_2024_dis):
        with pdfplumber.open(path_2024_dis) as pdf:
            for page in pdf.pages:
                for tbl in page.extract_tables():
                    for row in tbl:
                        row_c = [clean_text(c) for c in row]
                        if len(row_c) >= 9 and re.match(r"^\d+$", row_c[0]):
                            records.append({
                                "project_name": row_c[1],
                                "project_description": row_c[2],
                                "sector": row_c[3],
                                "project_type": row_c[4],
                                "constituency": row_c[5],
                                "ward": row_c[6],
                                "zone": row_c[7],
                                "location": row_c[6],
                                "amount_allocated_zmw": 0.0,
                                "approval_status": "DISAPPROVED",
                                "fiscal_year": 2024,
                                "justification_notes": row_c[9] if len(row_c) > 9 else row_c[8]
                            })

    df = pd.DataFrame(records)
    if not df.empty:
        # Standardize strings
        df["constituency"] = df["constituency"].str.upper().str.replace("BWANA MKUBW", "BWANA MKUBWA").str.strip()
        df["sector"] = df["sector"].str.upper().str.strip()
        df["project_type"] = df["project_type"].str.upper().str.strip()
        df["approval_status"] = df["approval_status"].str.upper().str.strip()
        df.insert(0, "project_id", [f"NCC-CDF-PRJ-{i+1:04d}" for i in range(len(df))])

    logger.info(f"Extracted {len(df)} CDF Community Project records.")
    return df


def extract_cdf_skills_bursaries():
    """
    Extracts and standardizes skills development bursary beneficiaries across all 4 constituencies.
    """
    logger.info("Extracting CDF Skills Development Bursaries...")
    records = []

    skills_files = [
        ("Ndola Central", "01-LiST-OF-APPROVED-CDF-2025-SKILLS-DEVELOPMENT-Ndola-Central-Constituency.pdf"),
        ("Bwana Mkubwa", "LIST-OF-APPROVED-CDF-2025-SKILLS-DEVELOPMENT-Bwana-Mkubwa_Constituency.pdf"),
        ("Chifubu", "LIST-OF-APPROVED-CDF-2025-SKILLS-DEVELOPMENT-Chifubu-constituency.pdf"),
        ("Kabushi", "LIST-OF-APPROVED-CDF-2025-SKILS-DEVELOPMENT-BENEFICARIES-KABUSHI-CONSTITUENCY.pdf"),
    ]

    for constituency_name, fname in skills_files:
        path = os.path.join(SOURCE_DIR, fname)
        if not os.path.exists(path):
            continue

        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    # Pattern matching student entry: S/N NAME NRC CONTACT WARD GENDER AGE INSTITUTION COURSE LEVEL DURATION STATUS ANNUAL_FEES
                    m = re.match(r"^(\d+)\s+([A-Z\s\'-]+?)\s+(\d{6}/\d{2}/\d|\d{9})\s+(\d{9,10})\s+([A-Z\s]+?)\s+([MF])\s+(\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2}|[\d,]+)$", line)
                    if m:
                        sn, name, nrc, contact, ward, gender, age, middle_blob, fees = m.groups()
                        records.append({
                            "constituency": constituency_name.upper(),
                            "student_name": clean_text(name),
                            "nrc_no": clean_text(nrc),
                            "contact_no": clean_text(contact),
                            "ward": clean_text(ward),
                            "gender": gender.upper(),
                            "age": int(age) if age.isdigit() else None,
                            "institution_and_course": clean_text(middle_blob),
                            "annual_fees_zmw": clean_amount(fees),
                            "academic_year": 2025,
                            "approval_status": "APPROVED"
                        })
                    else:
                        # Fallback for structured rows that start with number
                        m2 = re.match(r"^(\d+)\s+([A-Z\s\'-]+?)\s+(\d{6}/\d{2}/\d|\d{9})\s+(.+?)\s+([\d,]+\.\d{2}|[\d,]+)$", line)
                        if m2:
                            sn, name, nrc, middle_blob, fees = m2.groups()
                            # Extract gender and age if present in middle_blob
                            g_match = re.search(r"\b([MF])\b\s+(\d{2})\b", middle_blob)
                            gender = g_match.group(1) if g_match else "U"
                            age = int(g_match.group(2)) if g_match else None
                            records.append({
                                "constituency": constituency_name.upper(),
                                "student_name": clean_text(name),
                                "nrc_no": clean_text(nrc),
                                "contact_no": "",
                                "ward": "",
                                "gender": gender,
                                "age": age,
                                "institution_and_course": clean_text(middle_blob),
                                "annual_fees_zmw": clean_amount(fees),
                                "academic_year": 2025,
                                "approval_status": "APPROVED"
                            })

    df = pd.DataFrame(records)
    if not df.empty:
        df.drop_duplicates(subset=["constituency", "student_name", "nrc_no"], inplace=True)
        df.insert(0, "bursary_id", [f"NCC-CDF-SKL-{i+1:05d}" for i in range(len(df))])

    logger.info(f"Extracted {len(df)} Skills Development Bursary records.")
    return df


def extract_cdf_secondary_bursaries():
    """
    Extracts and standardizes secondary school boarding bursary beneficiaries across all 4 constituencies.
    """
    logger.info("Extracting CDF Secondary School Boarding Bursaries...")
    records = []

    sec_files = [
        ("Ndola Central", "LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-Ndola-Central.pdf"),
        ("Bwana Mkubwa", "LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-Bwana-Mkubwa_Constituency.pdf"),
        ("Chifubu", "LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-CHIFUBU-CONSTITUENCY.pdf"),
        ("Kabushi", "LIST-OF-APPROVED-CDF-2025-SECONDARY-BOARDING-KABUSHI-Constituency.pdf"),
    ]

    for constituency_name, fname in sec_files:
        path = os.path.join(SOURCE_DIR, fname)
        if not os.path.exists(path):
            continue

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for tbl in tables:
                        for row in tbl:
                            row_c = [clean_text(c) for c in row if c is not None]
                            if len(row_c) >= 7 and re.match(r"^\d+$", row_c[0]):
                                records.append({
                                    "constituency": constituency_name.upper(),
                                    "pupil_name": row_c[1],
                                    "ward": row_c[2] if len(row_c) > 2 else "",
                                    "gender": row_c[3] if len(row_c) > 3 else "",
                                    "age": int(row_c[4]) if len(row_c) > 4 and row_c[4].isdigit() else None,
                                    "grade_level": row_c[5] if len(row_c) > 5 else "",
                                    "parent_or_guardian_name": row_c[6] if len(row_c) > 6 else "",
                                    "school_name": row_c[8] if len(row_c) > 8 else (row_c[7] if len(row_c) > 7 else ""),
                                    "school_location": row_c[9] if len(row_c) > 9 else "Copperbelt",
                                    "annual_fees_zmw": clean_amount(row_c[-1]),
                                    "academic_year": 2025,
                                    "approval_status": "APPROVED"
                                })
                else:
                    # Text line extraction fallback
                    text = page.extract_text() or ""
                    for line in text.split("\n"):
                        m = re.match(r"^(\d+)\s+([A-Z\s\'-]+?)\s+([A-Z\s]+?)\s+([MF])\s+(\d{1,2})\s+(\d{1,2}|GRADE\s+\d+)\s+(.+?)\s+([\d,]+)$", line.strip())
                        if m:
                            sn, name, ward, gender, age, grade, parent_school, fees = m.groups()
                            records.append({
                                "constituency": constituency_name.upper(),
                                "pupil_name": clean_text(name),
                                "ward": clean_text(ward),
                                "gender": gender.upper(),
                                "age": int(age) if age.isdigit() else None,
                                "grade_level": clean_text(grade),
                                "parent_or_guardian_name": "",
                                "school_name": clean_text(parent_school),
                                "school_location": "Ndola/Copperbelt",
                                "annual_fees_zmw": clean_amount(fees),
                                "academic_year": 2025,
                                "approval_status": "APPROVED"
                            })

    df = pd.DataFrame(records)
    if not df.empty:
        df.drop_duplicates(subset=["constituency", "pupil_name"], inplace=True)
        df.insert(0, "secondary_bursary_id", [f"NCC-CDF-SEC-{i+1:04d}" for i in range(len(df))])

    logger.info(f"Extracted {len(df)} Secondary Boarding Bursary records.")
    return df


def extract_cdf_empowerment_grants_loans():
    """
    Extracts and standardizes CDF empowerment grants and loans for youth, women, and community clubs.
    """
    logger.info("Extracting CDF Empowerment Grants and Loans...")
    records = []

    # Grants files
    grant_files = [
        ("Ndola Central", "LIST-OF-APPROVED-CDF-2025-EMPOWERNMENT-GRANTS-NDOLA-CENTRAL-Constituency-1.pdf", "GRANT"),
        ("Bwana Mkubwa", "LIST-OF-APPROVED-CDF-2025-EMPWERMENT-GRANTS-BWANA-MKUBWA-Constituency-1.pdf", "GRANT"),
        ("Chifubu", "LIST-OF-APPROVED-CDF-2025-EMPOWERMENT-GRANTS-CHIFUBU-CONSTITUENCY-1.pdf", "GRANT"),
        ("Kabushi", "LIST-OF-APROVED-CDF-2025-EMPOWERMENT-GRANTS-KABUSHI-Constituency-1.pdf", "GRANT"),
        ("Ndola Central", "LIST-OF-APPROVED-CDF-2025-EMPOWERMRNT-LOANS-NDOLA-CENTRAL-CINSTITUENCY_1-2.pdf", "LOAN"),
        ("Bwana Mkubwa", "LIST-OF-APPROVED-CDF-2025-LOAN-BENEFICARIES-BWANA-MKUBWA-CONTITUENCY.pdf", "LOAN"),
        ("Chifubu", "LIST-OF-APPROVED-CDF2025-EMPOWERMENT-LOANS-CHIFUBU-CONSTITUENCY-Copy.pdf", "LOAN"),
    ]

    for constituency_name, fname, mechanism in grant_files:
        path = os.path.join(SOURCE_DIR, fname)
        if not os.path.exists(path):
            continue

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for tbl in tables:
                        for row in tbl:
                            row_c = [clean_text(c) for c in row if c is not None]
                            if len(row_c) >= 7 and re.match(r"^\d+$", row_c[0] if row_c[0] != "" else (row_c[1] if len(row_c)>1 else "")):
                                offset = 1 if row_c[0] == "" else 0
                                records.append({
                                    "constituency": constituency_name.upper(),
                                    "funding_type": mechanism,
                                    "group_or_applicant_name": row_c[offset + 1],
                                    "group_category": row_c[offset + 2] if len(row_c) > (offset + 2) else "COMMUNITY",
                                    "registration_no": row_c[offset + 3] if len(row_c) > (offset + 3) else "",
                                    "ward": row_c[offset + 4] if len(row_c) > (offset + 4) else "",
                                    "contact_person": row_c[offset + 5] if len(row_c) > (offset + 5) else "",
                                    "business_venture_type": row_c[offset + 7] if len(row_c) > (offset + 7) else "",
                                    "economic_sector": row_c[offset + 8] if len(row_c) > (offset + 8) else "AGRICULTURE/TRADE",
                                    "amount_approved_zmw": clean_amount(row_c[-1]),
                                    "allocation_year": 2025,
                                    "approval_status": "APPROVED"
                                })
                else:
                    text = page.extract_text() or ""
                    for line in text.split("\n"):
                        m = re.match(r"^(\d+)\s+([A-Z0-9\s\'-]+?)\s+(\d{4,12}|NONE|PENDING)\s+([A-Z\s]+?)\s+([A-Z\s]+?)\s+(\d{9,10})\s+(.+?)\s+([\d,]+\.\d{2}|[\d,]+)$", line.strip())
                        if m:
                            sn, group_name, reg, ward, contact_name, phone, venture, amt = m.groups()
                            records.append({
                                "constituency": constituency_name.upper(),
                                "funding_type": mechanism,
                                "group_or_applicant_name": clean_text(group_name),
                                "group_category": "COMMUNITY/YOUTH/WOMEN",
                                "registration_no": clean_text(reg),
                                "ward": clean_text(ward),
                                "contact_person": clean_text(contact_name),
                                "business_venture_type": clean_text(venture),
                                "economic_sector": "ENTERPRISE",
                                "amount_approved_zmw": clean_amount(amt),
                                "allocation_year": 2025,
                                "approval_status": "APPROVED"
                            })

    df = pd.DataFrame(records)
    if not df.empty:
        df.drop_duplicates(subset=["constituency", "group_or_applicant_name", "funding_type"], inplace=True)
        df.insert(0, "empowerment_id", [f"NCC-CDF-EMP-{i+1:04d}" for i in range(len(df))])

    logger.info(f"Extracted {len(df)} CDF Empowerment Grant and Loan records.")
    return df


def extract_municipal_budget_and_financials():
    """
    Extracts and standardizes Output-Based Budget (OBB) allocations and revenue/expenditure line items.
    """
    logger.info("Extracting Municipal Budget and Financials...")
    records = []

    budget_2026_path = os.path.join(SOURCE_DIR, "NDOLA-CITY-COUNCIL-2026-BUDGET-1.pdf")
    if os.path.exists(budget_2026_path):
        with pdfplumber.open(budget_2026_path) as pdf:
            current_programme = "Local Governance and Institutional Management"
            for page in pdf.pages:
                text = page.extract_text() or ""
                # Track programme headers
                prog_match = re.search(r"Programme\s*:\s*\d+\s*([A-Za-z\s]+)", text)
                if prog_match:
                    current_programme = prog_match.group(1).strip()

                tables = page.extract_tables()
                for tbl in tables:
                    for row in tbl:
                        row_c = [clean_text(c) for c in row if c is not None]
                        if len(row_c) >= 3:
                            # Look for financial line item rows
                            line_desc = row_c[0]
                            if any(k in line_desc.upper() for k in ["PERSONAL EMOLUMENTS", "USE OF GOODS", "TRANSFERS", "CAPITAL", "REVENUE", "LGEF", "RATES", "FEES", "GRANTS", "CDF"]):
                                amt_val = clean_amount(row_c[-1] if len(row_c) > 1 else 0)
                                if amt_val > 0:
                                    records.append({
                                        "fiscal_year": 2026,
                                        "programme_name": current_programme,
                                        "line_item_category": line_desc,
                                        "budget_type": "APPROVED_BUDGET",
                                        "amount_zmw": amt_val,
                                        "currency": "ZMW",
                                        "funding_source": "LGEF / Local Revenue / National Grants"
                                    })

    # Add 2024 Detailed OBB items
    obb_2024_path = os.path.join(SOURCE_DIR, "2024-OBB-Annual-Detailed-2.pdf")
    if os.path.exists(obb_2024_path):
        with pdfplumber.open(obb_2024_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for tbl in tables:
                    for row in tbl:
                        row_c = [clean_text(c) for c in row if c is not None]
                        if len(row_c) >= 3 and any(k in row_c[0].upper() for k in ["PERSONAL EMOLUMENTS", "USE OF GOODS", "CAPITAL", "GRANTS", "TOTAL"]):
                            amt_val = clean_amount(row_c[-1])
                            if amt_val > 0:
                                records.append({
                                    "fiscal_year": 2024,
                                    "programme_name": "Municipal Operational Budget",
                                    "line_item_category": row_c[0],
                                    "budget_type": "APPROVED_BUDGET",
                                    "amount_zmw": amt_val,
                                    "currency": "ZMW",
                                    "funding_source": "National Transfers & Council Own Revenues"
                                })

    df = pd.DataFrame(records)
    if not df.empty:
        df.drop_duplicates(inplace=True)
        df.insert(0, "budget_record_id", [f"NCC-FIN-{i+1:04d}" for i in range(len(df))])

    logger.info(f"Extracted {len(df)} Municipal Budget and Financial records.")
    return df


def extract_governance_and_resolutions():
    """
    Extracts council resolutions, committee minutes, and DDCC milestone records.
    """
    logger.info("Extracting Governance and Committee Resolutions...")
    records = []

    minute_files = [
        ("Full Council Ordinary", "MINUTES-OF-THE-ORDINARY-MEETING-OF-THE-COUNCIL-HELD-ON-1ST-JULY-2025.pdf", "2025-07-01"),
        ("Full Council Special", "MINUTES-OF-THE-SPECIAL-COUNCIL-MEETING-HELD-ON-4TH-APRIL-2025.pdf", "2025-04-04"),
        ("Planning Committee", "MINUTES-OF-PLANNING-HELD-ON-26TH-SEPTEMBER-2024.pdf", "2024-09-26"),
        ("Engineering Services Committee", "MINUTES-OF-ENGINEERING-SERVICES-COMMITTEE-HELD-ON-MONDAY-23RD-SEPTEMBER-2024.pdf", "2024-09-23"),
        ("Audit Committee", "MINUTES-OF-AUDIT-COMMITTEE-HELD-ON-25TH-SEPTEMBER-2024.pdf", "2024-09-25"),
        ("Legal Services Committee", "MINUTES-OF-LEGAL-SERVICES-ADMIN-HELD-ON-1ST-OCTOBER-2024.pdf", "2024-10-01"),
        ("Community Development Committee", "MINUTES-OFCOMMUNITY-DEVELOPMENT-HELD-ON-16TH-SEPTEMBER-2024.pdf", "2024-09-16"),
        ("DDCC Quarterly", "DDCC-MINUTES-OF-2ND-QUARTER-MEETING_22-JULY-2025.pdf", "2025-07-22"),
        ("DDCC Quarterly", "FINAL-DDCC-MINUTES-OF-3RD-QUARTER-MEETING_24-SEPTEMBER-2025.pdf", "2025-09-24"),
    ]

    for committee_name, fname, meeting_date in minute_files:
        path = os.path.join(SOURCE_DIR, fname)
        if not os.path.exists(path):
            continue

        with pdfplumber.open(path) as pdf:
            full_text = ""
            for p in pdf.pages:
                full_text += (p.extract_text() or "") + "\n"

            # Look for minute items / agenda headings (e.g., MIN. NCC/..., RESOLVED:, ITEM)
            items = re.findall(r"(MIN(?:UTE)?\s*[\.\/A-Z0-9\s\/-]+?)(?=\n[A-Z\s]{4,}|\nMIN|\Z)", full_text, re.DOTALL)
            if not items:
                # fallback extraction by paragraphs
                paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 80 and "RESOLVED" in p]
                for p_idx, p in enumerate(paragraphs[:15]):
                    records.append({
                        "committee_or_body": committee_name,
                        "meeting_date": meeting_date,
                        "agenda_item_or_ref": f"ITEM-{p_idx+1:02d}",
                        "resolution_summary": clean_text(p[:300]),
                        "governance_area": "Municipal Administration & Infrastructure",
                        "status": "ADOPTED"
                    })
            else:
                for item_idx, it in enumerate(items[:20]):
                    records.append({
                        "committee_or_body": committee_name,
                        "meeting_date": meeting_date,
                        "agenda_item_or_ref": clean_text(it[:60]),
                        "resolution_summary": clean_text(it[60:400]),
                        "governance_area": "Council Governance & Service Delivery",
                        "status": "ADOPTED"
                    })

    df = pd.DataFrame(records)
    if not df.empty:
        df.drop_duplicates(inplace=True)
        df.insert(0, "resolution_id", [f"NCC-RES-{i+1:04d}" for i in range(len(df))])

    logger.info(f"Extracted {len(df)} Governance and Resolution records.")
    return df


def main():
    os.makedirs(TABULAR_DIR, exist_ok=True)

    datasets = [
        ("ndola_council_cdf_community_projects_2024_2025", extract_cdf_community_projects()),
        ("ndola_council_cdf_skills_bursaries_2025", extract_cdf_skills_bursaries()),
        ("ndola_council_cdf_secondary_boarding_bursaries_2025", extract_cdf_secondary_bursaries()),
        ("ndola_council_cdf_empowerment_grants_loans_2025", extract_cdf_empowerment_grants_loans()),
        ("ndola_council_municipal_budget_and_expenditure_2024_2026", extract_municipal_budget_and_financials()),
        ("ndola_council_governance_and_committee_resolutions_2024_2025", extract_governance_and_resolutions()),
    ]

    for desc, df in datasets:
        filename = f"db-unza26-csc4792-{desc}.csv"
        out_path = os.path.join(TABULAR_DIR, filename)
        df.to_csv(out_path, sep="|", index=False, encoding="utf-8")
        logger.info(f"Saved {len(df)} rows to {out_path} (sep='|')")

    logger.info("All tabular datasets successfully extracted, cleaned, and exported.")


if __name__ == "__main__":
    main()
