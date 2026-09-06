"""Standalone CLI runner for Nowcoder (牛客网) Campus Recruitment Spider.
Usage:
    python backend/src/services/spiders/run_nowcoder.py [--pages 5] [--size 50] [--since 2026-07-01]
"""
import sys
import os
import argparse
import asyncio
import logging

# Ensure project root & backend are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.services.spiders.nowcoder_spider import NowcoderSpider
from src.repositories.job_repository import JobRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("run_nowcoder")


async def main():
    parser = argparse.ArgumentParser(description="Fetch Nowcoder campus postings into public DB.")
    parser.add_argument("--pages", type=int, default=5, help="Maximum number of pages to fetch (default: 5)")
    parser.add_argument("--size", type=int, default=50, help="Number of items per request page (default: 50)")
    parser.add_argument("--since", type=str, default="2026-07-01", help="Earliest date cutoff (YYYY-MM-DD)")
    args = parser.parse_args()

    logger.info("Initializing NowcoderSpider (pages=%d, size=%d, since=%s)...", args.pages, args.size, args.since)
    repo = JobRepository()
    spider = NowcoderSpider(repo=repo)

    total_affected = await spider.run(
        since_date=args.since,
        max_pages=args.pages,
        page_size=args.size,
    )
    logger.info("Sync finished! Total jobs affected in DB: %d", total_affected)


if __name__ == "__main__":
    asyncio.run(main())
