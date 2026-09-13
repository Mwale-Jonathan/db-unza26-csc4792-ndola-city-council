#!/usr/bin/env python3
"""
Orchestration Runner for Ndola City Council Data Mining Pipeline
Course: 2025/26 CSC 4792 - Data Mining and Warehousing
"""

import sys
import logging
from scraper import main as run_scraper
from document_downloader import main as run_downloader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== STEP 1: EXECUTING NDOLA COUNCIL WEB SCRAPER & TABLE EXTRACTOR ===")
    try:
        run_scraper()
    except Exception as e:
        logger.error(f"Error during scraping: {e}")

    logger.info("=== STEP 2: EXECUTING NDOLA COUNCIL DOCUMENT DOWNLOADER ===")
    try:
        run_downloader()
    except Exception as e:
        logger.error(f"Error during downloading: {e}")

    logger.info("=== STEP 1 (DATA ACQUISITION) COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
