#!/usr/bin/env python3

import os
import csv
from pathlib import Path
import shutil

# Path to your summary CSV
CSV_PATH = "gpu_test_summary.csv"

# Root path where your test .amber files are
TEST_SUITE_ROOT = "../all_tests"

# Output directory to collect failed variants
OUTPUT_DIR = "../failed_variants"

# Copy or symlink? Set to True to copy, False to symlink
COPY_FILES = True

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(CSV_PATH, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            gpu_name = row['GPU']
            suite_dirname = row['Output Directory']
            failed_variants = row['Failed Tests']

            if not failed_variants.strip():  # Skip rows with no failed variants
                continue

            suite_path = Path(TEST_SUITE_ROOT) / suite_dirname
            target_dir = Path(OUTPUT_DIR) / gpu_name/ suite_dirname
            target_dir.mkdir(parents=True, exist_ok=True)

            for variant in failed_variants.split(";"):
                variant = variant.strip()
                source_file = suite_path / f"{variant}.comp"
                source_json = suite_path / f"{variant}.json"
                dest_file = target_dir / f"{variant}.comp"
                dest_json = target_dir / f"{variant}.json"

                if source_file.exists():
                    shutil.copy(source_file, dest_file)
                    shutil.copy(source_json, dest_json)
                else:
                    print(f"⚠️ Warning: {source_file} does not exist")

    print(f"\n✅ Done. Extracted failed variants into: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
