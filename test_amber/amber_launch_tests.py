# -----------------------------------------------------------------------
# amber_launch_tests.py
# Authors: Hari Raval
# -----------------------------------------------------------------------
import sys
import os
import argparse
import subprocess

DIR_GENERIC = [
                    "../all_tests/syn_branch_syn",
                       "../all_tests/syn_branch_syn_relax",
                       "../all_tests/syn_branch_syn_release",
                       "../all_tests/syn_lock_step",
                       "../all_tests/syn_lock_step_relax",
                       "../all_tests/syn_lock_step_release",
                       "../all_tests/syn_subgroup_op",
                       "../all_tests/syn_subgroup_op_relax",
                       "../all_tests/syn_subgroup_op_release",
                       "../all_tests/syn_memory_converge",
                       "../all_tests/syn_memory_converge_atomic",
                       ]
    
DIR_CORE  = [
                                "../all_tests_core/syn_branch_syn_rw",
                                "../all_tests_core/syn_branch_syn_wr",
                                "../all_tests_core/syn_branch_syn_ww",
                                "../all_tests_core/syn_lock_step_rw",
                                "../all_tests_core/syn_lock_step_wr",
                                "../all_tests_core/syn_lock_step_ww",
                                "../all_tests_core/syn_subgroup_op_rw",
                                "../all_tests_core/syn_subgroup_op_wr",
                                "../all_tests_core/syn_subgroup_op_ww",
                                "../all_tests_core/syn_memory_converge_ww",
                        ]



SELECTION = {
    "core": DIR_CORE,
    "generic": DIR_GENERIC,
}
# run the amber_test_driver.py script with all input directories available in Input_Files
def main():
    p = argparse.ArgumentParser(description="Run Amber test suites")
    p.add_argument("suite", choices=SELECTION, help="which directory list to run")
    p.add_argument("--android", action="store_true", help="Android tests")
    p.add_argument("--serial", help="serial number of device (if more than one attached with adb)")
    p.add_argument("--device", help="vulkan device id (if more than 1 vulkan device available)")
    args = p.parse_args()


    for name in SELECTION[args.suite]:
        cmd = ["python3", "amber_test_driver.py", name, "1"]
        if args.android:
            cmd.append("--android")
        if args.serial:
            cmd += ["--serial", args.serial]
        if args.device:
            cmd += ["--device", args.device]
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
