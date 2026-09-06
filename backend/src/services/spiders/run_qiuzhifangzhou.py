"""CLI entrypoint script to execute Qiuzhifangzhou job crawler."""
import asyncio
import argparse
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.spiders.qiuzhifangzhou_spider import QiuzhifangzhouSpider
from src.db import init_public_db
from src.config import config

async def main():
    parser = argparse.ArgumentParser(description="Run Qiuzhifangzhou job crawler")
    parser.add_argument("--table", type=str, default="latest", choices=["latest", "campus", "state_owned", "intern"], help="Job category to crawl")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of items to crawl")
    args = parser.parse_args()

    print(f"[*] Initializing database at {config.public_db_path}...")
    await init_public_db()

    print(f"[*] Starting Qiuzhifangzhou spider (table={args.table}, limit={args.limit})...")
    spider = QiuzhifangzhouSpider()
    result = await spider.crawl_and_save(table=args.table, limit=args.limit)

    print(f"[+] Crawler finished: fetched={result['fetched']}, saved/updated={result['saved']}")

if __name__ == "__main__":
    asyncio.run(main())
