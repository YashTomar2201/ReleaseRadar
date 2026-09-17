"""ReleaseRadar — Play Store review scraper.

Pulls newest-first reviews for each configured app, anonymizes the
reviewer identity, and writes one parquet file per page immediately
(crash-safe: a failure at review 180k still keeps everything already
written). Intended to be re-run weekly — duplicates are removed later
at the dbt staging layer by `reviewId`.

Usage:
    python src/scrape/scrape_reviews.py                 # scrape all apps
    python src/scrape/scrape_reviews.py --app phonepe    # single app
    python src/scrape/scrape_reviews.py --max 20000       # override per-app cap
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

import pandas as pd
import yaml
from google_play_scraper import Sort, reviews

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "apps.yaml"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "reviews"

# Consecutive empty/duplicate batches before we conclude the Play Store's
# pagination has stalled (rather than a transient hiccup).
STALL_LIMIT = 4

# An empty batch before ANY reviews have been collected for this app is
# treated as a transient failure (e.g. rate-limiting after a long
# scrape of a previous app) and retried, rather than as genuine
# pagination exhaustion -- that diagnosis only makes sense once we've
# actually reached the end of real data. See decision_log.md, 2026-09-18.
EMPTY_FIRST_BATCH_RETRY_LIMIT = 5
EMPTY_FIRST_BATCH_BACKOFF_SECONDS = 45


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def anonymize(df: pd.DataFrame) -> pd.DataFrame:
    """Replace the reviewer's display name with a stable one-way hash.
    We never store the raw username — only enough to (optionally) dedupe
    reviewers within our own dataset."""
    df["user_hash"] = df["userName"].astype(str).map(
        lambda u: hashlib.sha256(u.encode("utf-8")).hexdigest()[:16]
    )
    return df.drop(columns=["userName", "userImage"], errors="ignore")


def scrape_app(app_key: str, app_id: str, scrape_cfg: dict, max_override: int | None = None) -> int:
    max_reviews = max_override or scrape_cfg["max_reviews_per_app"]
    batch_size = scrape_cfg["batch_size"]
    sleep_seconds = scrape_cfg["sleep_seconds"]

    out_dir = RAW_DIR / app_key
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

    token = None
    total = 0
    page = 0
    stall_count = 0
    last_total = 0
    empty_first_batch_retries = 0
    t0 = time.time()

    print(f"[{app_key}] starting scrape, target={max_reviews:,} reviews")

    while total < max_reviews:
        try:
            batch, token = reviews(
                app_id,
                lang=scrape_cfg["lang"],
                country=scrape_cfg["country"],
                sort=Sort.NEWEST,
                count=batch_size,
                continuation_token=token,
            )
        except Exception as e:
            print(f"[{app_key}] request error: {e}; backing off 30s")
            time.sleep(30)
            continue

        if not batch:
            if total == 0:
                # Nothing collected yet -- almost certainly a transient
                # issue (rate-limit, network blip), not real exhaustion.
                empty_first_batch_retries += 1
                if empty_first_batch_retries > EMPTY_FIRST_BATCH_RETRY_LIMIT:
                    print(f"[{app_key}] FAILED: empty batch on every attempt "
                          f"({empty_first_batch_retries}) before collecting any reviews -- giving up")
                    break
                wait = EMPTY_FIRST_BATCH_BACKOFF_SECONDS * empty_first_batch_retries
                print(f"[{app_key}] empty first batch (attempt {empty_first_batch_retries}/"
                      f"{EMPTY_FIRST_BATCH_RETRY_LIMIT}) -- likely transient, retrying in {wait}s")
                time.sleep(wait)
                token = None  # reset in case the token itself is the problem
                continue
            else:
                # We already have real data -- this is genuine pagination
                # exhaustion (confirmed pattern from the Phase 1 depth test).
                print(f"[{app_key}] empty batch at n={total:,} -- Play Store pagination exhausted")
                break

        df = anonymize(pd.DataFrame(batch))
        df["app_key"] = app_key
        df["scraped_at"] = pd.Timestamp.now()
        out_path = out_dir / f"{run_id}_p{page:05d}.parquet"
        df.to_parquet(out_path, index=False)

        total += len(df)
        page += 1

        if total == last_total:
            stall_count += 1
            if stall_count >= STALL_LIMIT:
                print(f"[{app_key}] stalled (no new reviews for {STALL_LIMIT} batches) at n={total:,} -- stopping")
                break
        else:
            stall_count = 0
        last_total = total

        if page % 25 == 0:
            elapsed = time.time() - t0
            oldest = pd.to_datetime(df["at"]).min()
            print(f"[{app_key}] {total:,} reviews | oldest so far: {oldest} | {elapsed:.0f}s elapsed")

        if token is None or getattr(token, "token", None) is None:
            print(f"[{app_key}] continuation token exhausted at n={total:,}")
            break

        time.sleep(sleep_seconds)

    elapsed = time.time() - t0
    print(f"[{app_key}] DONE: {total:,} reviews across {page} pages in {elapsed:.0f}s\n")
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", help="scrape only this app key (default: all configured apps)")
    parser.add_argument("--max", type=int, help="override max_reviews_per_app from config")
    args = parser.parse_args()

    cfg = load_config()
    apps = cfg["apps"]
    scrape_cfg = cfg["scrape"]

    if args.app:
        if args.app not in apps:
            print(f"Unknown app key '{args.app}'. Available: {list(apps)}", file=sys.stderr)
            sys.exit(1)
        apps = {args.app: apps[args.app]}

    cooldown = scrape_cfg.get("inter_app_cooldown_seconds", 0)
    summary = {}
    for i, (key, meta) in enumerate(apps.items()):
        if i > 0 and cooldown:
            print(f"cooling down {cooldown}s before next app to avoid rate-limit carryover...")
            time.sleep(cooldown)
        summary[key] = scrape_app(key, meta["id"], scrape_cfg, max_override=args.max)

    print("=== SCRAPE SUMMARY ===")
    for key, n in summary.items():
        print(f"  {key}: {n:,} reviews")


if __name__ == "__main__":
    main()
