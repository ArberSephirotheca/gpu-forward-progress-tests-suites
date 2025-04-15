#!/usr/bin/env python3

import subprocess
from pathlib import Path
import os

# Directory containing failed variants
FAILED_DIR = Path("/opt/reduce")

# Directory containing reduction config files
REDUCE_CONFIG_DIR = Path("/opt/reduce")

# Interestingness test script name
INTERESTINGNESS_TEST = "interestingness_test"

# Output root directory
OUTPUT_ROOT = Path("reduction_results")

# Dry run (set to True to just print commands)
DRY_RUN = False

def main():
    if not FAILED_DIR.exists():
        print(f"❌ {FAILED_DIR} does not exist.")
        return

    for shader_file in FAILED_DIR.rglob("*.comp"):
        suite_name = shader_file.parent.relative_to(FAILED_DIR)
        variant_name = shader_file.stem
        config_path = FAILED_DIR / Path(suite_name) / f"{variant_name}.json"
        if not config_path.exists():
            print(f"⚠️  ❌ {shader_file} — missing config: {config_path}")
            return
        output_dir = OUTPUT_ROOT / suite_name / variant_name
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "glsl-reduce",
            config_path,
            INTERESTINGNESS_TEST,
            "--output", str(output_dir),
            str(shader_file)
        ]

        print(f"🛠️  Reducing {shader_file} → {output_dir}")
        if not DRY_RUN:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to reduce {shader_file}")
                print(result.stderr)
            else:
                print("✅ Done.")

if __name__ == "__main__":
    main()
