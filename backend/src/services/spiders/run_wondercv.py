#!/usr/bin/env python3
"""CLI runner for WonderCV (超级简历) campus spider.
Usage:
    python -m src.services.spiders.run_wondercv --pages 2
"""
import sys
import asyncio
import argparse
import logging
from src.services.spiders.wondercv_spider import WondercvSpider
from src.repositories.job_repository import JobRepository
from src.db import init_public_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("run_wondercv")

async def main():
    parser = argparse.ArgumentParser(description="WonderCV Campus Job Spider CLI")
    parser.add_argument("--pages", type=int, default=160, help="Max pages to crawl (default: 160)")
    parser.add_argument("--since", type=str, default="2026-08-01", help="Date cutoff YYYY-MM-DD (default: 2026-08-01)")
    args = parser.parse_args()

    # Ensure public database and tables are initialized
    await init_public_db()

    logger.info(f"Starting WonderCV spider crawl for up to {args.pages} pages (cutoff: {args.since})...")
    repo = JobRepository()
    spider = WondercvSpider(repo=repo)

    result = await spider.crawl_and_save(since_date=args.since, max_pages=args.pages)
    logger.info(f"Crawl completed successfully: {result}")
    print(f"\n[Result] WonderCV Spider finished: Fetched={result['fetched']}, Saved={result['saved']}")

if __name__ == "__main__":
    asyncio.run(main())
