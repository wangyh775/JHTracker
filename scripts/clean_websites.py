#!/usr/bin/env python3
"""
Clean_websites.py — Clean company website URLs in career-tracker DB.

Strategy:
1. Build a company→official_website mapping from records.json + records_extra.json
2. For each company in the DB:
   a. If website is NULL/empty → fill from records mapping if available
   b. If website is a job-board/career-portal URL (not the company's own domain) → optionally replace with the records' official website
   c. Report what's still broken
3. Don't touch already-good websites (non-NULL, non-empty, non-job-board patterns that match real company domains)
"""

import json
import re
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tracker.db')
RECORDS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'records.json')
RECORDS_EXTRA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'records_extra.json')

# Normalize company name for matching
def normalize_name(name):
    """Normalize a company name for fuzzy matching."""
    if not name:
        return ""
    name = name.strip()
    # Remove parenthetical suffixes like (China), （中国）, (Inovance), etc.
    name = re.sub(r'[（(][^)）]*[)）]', '', name)
    # Remove common suffixes
    name = re.sub(r'\s*（中国）\s*$', '', name)
    name = re.sub(r'\s*\(China\)\s*$', '', name)
    # Remove "集团" and similar
    name = name.replace('集团', '')
    # Normalize whitespace
    name = re.sub(r'\s+', '', name)
    return name.lower().strip()

def extract_domain(url):
    """Extract the main domain from a URL."""
    if not url:
        return ""
    m = re.search(r'https?://([^/]+)', url)
    if m:
        return m.group(1).lower()
    return ""

# Load records files
def load_records(path):
    """Load a records.json file and return a dict mapping company name → official website."""
    mapping = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  WARN: Cannot load {path}: {e}")
        return mapping
    
    if not isinstance(data, dict) or 'fields' not in data or 'rows' not in data:
        print(f"  WARN: {path} has unexpected format")
        return mapping
    
    try:
        website_idx = data['fields'].index('官网')
        name_idx = data['fields'].index('公司名称')
    except ValueError as e:
        print(f"  WARN: {path} missing required field: {e}")
        return mapping
    
    for row in data['rows']:
        if len(row) > max(name_idx, website_idx):
            company_name = row[name_idx].strip() if row[name_idx] else ""
            website = row[website_idx].strip() if row[website_idx] else ""
            if company_name and website:
                mapping[company_name] = website
                # Also add normalized version
                norm = normalize_name(company_name)
                if norm and norm != company_name:
                    mapping[norm] = website
    
    print(f"  Loaded {len(mapping)} entries from {os.path.basename(path)}")
    return mapping

def is_job_board_url(url):
    """Check if a URL is a job-board or recruitment portal (not a company homepage)."""
    if not url:
        return True
    url_lower = url.lower()
    # These are recruitment/career portal domains, not the company's own homepage
    job_board_domains = [
        'zhipin.com', 'bosszhipin.com', 'liepin.com', 'lagou.com',
        '51job.com', 'zhilian.com', 'zhaopin.com', 'jobcenters',
        'jobcareer', 'zhiye.com',
    ]
    domain = extract_domain(url)
    for jd in job_board_domains:
        if jd in domain:
            return True
    return False

def is_job_page_url(url):
    """Check if the URL looks like a job/recruit/careers page rather than a main company site."""
    if not url:
        return True
    # These are fine as they are official corporate career portals
    # But we might want to replace with the main homepage from records
    url_lower = url.lower()
    path = url_lower.split('://', 1)[-1] if '://' in url_lower else url_lower
    # Check for job/career path segments
    if '/career' in path or '/recruit' in path or '/job' in path or '/campus' in path or '/zhiye' in path:
        return True
    return False

def main():
    print("=" * 60)
    print("CAREER TRACKER — Website Cleanup")
    print("=" * 60)
    
    # Load records
    print("\n[1] Loading records files...")
    records_map = {}
    records_map.update(load_records(RECORDS_PATH))
    records_map.update(load_records(RECORDS_EXTRA_PATH))
    print(f"  Total unique company entries in records: {len(records_map)}")
    
    # Connect to DB
    print("\n[2] Connecting to DB...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all companies
    cur.execute('SELECT id, name, website FROM companies ORDER BY id')
    all_companies = cur.fetchall()
    print(f"  Total companies in DB: {len(all_companies)}")
    
    # Stats counters
    null_websites = []
    boss_websites = []
    job_board_websites = []
    fixed_from_records = []
    still_null = []
    unknown = []
    
    # Build a reverse lookup by normalized name
    records_by_norm = {}
    for raw_name, website in records_map.items():
        norm = normalize_name(raw_name)
        if norm not in records_by_norm:
            records_by_norm[norm] = website
    
    print(f"\n[3] Analyzing websites...")
    for row in all_companies:
        cid = row['id']
        name = row['name']
        website = row['website']
        norm_name = normalize_name(name)
        
        if not website or website.strip() == '':
            null_websites.append((cid, name, website))
            # Try to find from records
            if norm_name in records_by_norm:
                new_website = records_by_norm[norm_name]
                if new_website:
                    fixed_from_records.append((cid, name, website, new_website))
                    continue
            still_null.append((cid, name, None))
            continue
        
        if is_job_board_url(website):
            boss_websites.append((cid, name, website))
            continue
        
        # Check if it's a job/career page (maybe we have a better homepage from records)
        # We'll note this but not replace unless the records has a CLEARLY better option
        if is_job_page_url(website):
            # Check if records has a different URL for this company
            if norm_name in records_by_norm:
                rec_website = records_by_norm[norm_name]
                if rec_website and rec_website != website:
                    # Only replace if the records URL is clearly different (not also a job page)
                    # or if the records URL is the main domain
                    rec_domain = extract_domain(rec_website)
                    cur_domain = extract_domain(website)
                    if rec_domain and cur_domain and rec_domain != cur_domain:
                        # Different domain — records might have a better homepage
                        # But we need to be careful: some companies have separate career domains
                        job_board_websites.append((cid, name, website, rec_website))
    
    print(f"\n[4] Results:")
    print(f"  Companies with NULL/empty websites: {len(null_websites)}")
    print(f"  Companies with job-board URLs: {len(boss_websites)}")
    print(f"  Companies with career/job page URLs (possible upgrade): {len(job_board_websites)}")
    print(f"  Companies fixable from records (NULL → website): {len(fixed_from_records)}")
    print(f"  Companies still NULL after matching: {len(still_null)}")
    
    # Apply fixes: fill NULL websites from records
    print(f"\n[5] Applying fixes...")
    updates = 0
    for cid, name, old_website, new_website in fixed_from_records:
        cur.execute('UPDATE companies SET website = ? WHERE id = ?', (new_website, cid))
        updates += 1
        print(f"  ✓ [{cid}] {name}: None → {new_website}")
    
    conn.commit()
    print(f"\n  Applied {updates} updates (NULL → official website from records)")
    
    # Report on career/job page URLs that could be upgraded
    print(f"\n[6] Career/job page URLs (not urgent, but records has a different URL):")
    for cid, name, website, rec_website in job_board_websites:
        print(f"  ? [{cid}] {name}")
        print(f"      Current: {website}")
        print(f"      Records:  {rec_website}")
    
    # Report still-null
    print(f"\n[7] Still NULL/empty websites (need manual lookups):")
    for cid, name, _ in still_null:
        print(f"  ✗ [{cid}] {name}")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY")
    print(f"{'='*60}")
    total_broken = len(still_null) + len(boss_websites)
    print(f"  Fixed: {updates} companies (NULL → official website from records)")
    print(f"  Still broken: {total_broken} companies")
    print(f"    - NULL/empty: {len(still_null)}")
    print(f"    - Job board URLs: {len(boss_websites)}")
    print(f"  Career page URLs (optional upgrade): {len(job_board_websites)}")
    
    conn.close()

if __name__ == '__main__':
    main()