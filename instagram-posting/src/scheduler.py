#!/usr/bin/env python3
"""
Instagram Posting Scheduler — Automated 2-Hour Cycle
Posts to Instagram every 2 hours with geographic distribution
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Schedule configuration
SCHEDULE_FILE = CONFIG_DIR / "instagram_schedule_2h.json"
CYCLE_HOURS = 2
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 60

# Setup logging
LOG_FILE = LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# SCHEDULE LOADER
# ============================================================================

def load_schedule():
    """Load schedule configuration from JSON"""
    try:
        with open(SCHEDULE_FILE, "r") as f:
            schedule = json.load(f)
        logger.info(f"[OK] Schedule loaded from: {SCHEDULE_FILE.name}")
        return schedule
    except FileNotFoundError:
        logger.error(f"[FAIL] Schedule file not found: {SCHEDULE_FILE}")
        return None
    except json.JSONDecodeError:
        logger.error(f"[FAIL] Invalid JSON in schedule file")
        return None

def get_next_execution_time(schedule, current_hour=None):
    """Calculate next execution time based on schedule"""
    if current_hour is None:
        current_hour = datetime.now().hour
    
    active_hours = schedule.get("active_hours", {})
    start_hour = active_hours.get("start", 9)
    end_hour = active_hours.get("end", 23)
    interval = schedule.get("interval_hours", 2)
    
    now = datetime.now()
    
    # Check if outside active window
    if current_hour < start_hour or current_hour >= end_hour:
        next_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        if next_time <= now:
            next_time += timedelta(days=1)
        return next_time
    
    # Calculate next execution within active window
    next_hour = ((current_hour - start_hour) // interval + 1) * interval + start_hour
    if next_hour >= end_hour:
        next_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        next_time += timedelta(days=1)
    else:
        next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    
    return next_time

# ============================================================================
# UPLOADER EXECUTION
# ============================================================================

def run_master_post_generator():
    """Execute the master post generator script"""
    generator_script = PROJECT_ROOT / "src" / "master_post_v2.py"
    
    if not generator_script.exists():
        logger.error(f"[FAIL] Master post generator not found: {generator_script}")
        return False
    
    logger.info(f"\n{'='*70}")
    logger.info(f"GENERATING NEW AI CHRONICLE POST")
    logger.info(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(generator_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("[OK] Post generation completed successfully")
            if result.stdout:
                logger.info(f"Output:\n{result.stdout}")
            return True
        else:
            logger.error(f"[FAIL] Post generation failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"Error:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("[FAIL] Post generation timeout (60 seconds exceeded)")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Execution error: {str(e)}")
        return False

# ============================================================================
# SCHEDULER LOOP
# ============================================================================

def run_scheduler_loop(duration_hours=24):
    """Run scheduler for specified duration"""
    logger.info("\n" + "=" * 70)
    logger.info("INSTAGRAM POSTING SCHEDULER")
    logger.info("=" * 70)
    
    schedule = load_schedule()
    if not schedule:
        logger.error("[FAIL] Cannot start without valid schedule")
        return False
    
    end_time = datetime.now() + timedelta(hours=duration_hours)
    execution_count = 0
    
    while datetime.now() < end_time:
        now = datetime.now()
        next_exec = get_next_execution_time(schedule)
        
        if now >= next_exec:
            execution_count += 1
            logger.info(f"\n[POST #{execution_count}] Starting post generation at {now.strftime('%H:%M:%S')}")
            
            success = run_master_post_generator()
            
            if success:
                logger.info(f"[OK] Post #{execution_count} generated successfully")
            else:
                logger.warning(f"[WARN] Post #{execution_count} generation failed")
            
            # Sleep until next window
            next_exec = get_next_execution_time(schedule)
            sleep_duration = (next_exec - datetime.now()).total_seconds()
            logger.info(f"[INFO] Next post scheduled for {next_exec.strftime('%H:%M:%S')}")
            logger.info(f"[INFO] Sleeping for {int(sleep_duration / 60)} minutes...")
            time.sleep(max(1, sleep_duration))
        else:
            # Sleep for 1 minute and check again
            sleep_duration = min(60, (next_exec - now).total_seconds())
            time.sleep(sleep_duration)
    
    logger.info(f"\n[OK] Scheduler completed. Total executions: {execution_count}")
    return True

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main scheduler entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Instagram Posting Scheduler - The AI Chronicle")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Generate and post one master post (no scheduling)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=24,
        help="Scheduler duration in hours (default: 24)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test 2-hour schedule calculation without generating posts"
    )
    
    args = parser.parse_args()
    
    if args.once:
        logger.info("Generating single master post...")
        return run_master_post_generator()
    elif args.test:
        logger.info("Testing schedule calculation...")
        schedule = load_schedule()
        if schedule:
            for hour in range(24):
                next_exec = get_next_execution_time(schedule, current_hour=hour)
                logger.info(f"Hour {hour:02d}:00 -> Next: {next_exec.strftime('%H:%M:%S')}")
        return True
    else:
        logger.info(f"Starting scheduler for {args.duration} hour(s)...")
        return run_scheduler_loop(duration_hours=args.duration)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n[INFO] Scheduler interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[FAIL] Fatal error: {str(e)}")
        sys.exit(1)
