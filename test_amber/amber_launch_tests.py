# -----------------------------------------------------------------------
# amber_launch_tests.py
# Authors: Hari Raval
# -----------------------------------------------------------------------
import sys
import os
import argparse


# run the amber_test_driver.py script with all input directories available in Input_Files
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--android', action='store_true', help='Android tests')
    parser.add_argument('--serial', help='serial number of device (if more than one attached with adb)')
    parser.add_argument('--device', help='vulkan device id (if more than 1 vulkan device available)')

    args = parser.parse_args()

    directory_names = [
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
                       "../all_tests/syn_rr",
                       "../all_tests/syn_rr_rwr",
                       "../all_tests/syn_rr_wrw",
                       ]
    
    directory_names_core = [
                               "../all_tests_core/syn_branch_syn_release",
                                "../all_tests_core/syn_lock_step_release",
                                "../all_tests_core/syn_subgroup_op_release",
                                "../all_tests_core/syn_branch_syn_rwr",
                                "../all_tests_core/syn_branch_syn_wrw",
                                "../all_tests_core/syn_branch_syn_rr",
                                "../all_tests_core/syn_lock_step_rwr",
                                "../all_tests_core/syn_lock_step_wrw",
                                "../all_tests_core/syn_lock_step_rr",
                                "../all_tests_core/syn_subgroup_op_rwr",
                                "../all_tests_core/syn_subgroup_op_wrw",
                                "../all_tests_core/syn_subgroup_op_rr",
                        ]

    directory_names_intel = [
                                "../all_tests_fixed_subgroup/syn_branch_syn",
                                "../all_tests_fixed_subgroup/syn_branch_syn_relax",
                                "../all_tests_intel/syn_branch_syn_release",
                                "../all_tests_fixed_subgroup/syn_lock_step",
                                "../all_tests_fixed_subgroup/syn_lock_step_relax",
                                "../all_tests_fixed_subgroup/syn_lock_step_release",
                                "../all_tests_fixed_subgroup/syn_subgroup_op",
                                "../all_tests_fixed_subgroup/syn_subgroup_op_relax",
                                "../all_tests_fixed_subgroup/syn_subgroup_op_release",
                                "../all_tests_fixed_subgroup/syn_memory_converge",
                                "../all_tests_fixed_subgroup/syn_memory_converge_atomic"
                            ]
    directory_names_intel_core = [
                                "../all_tests_fixed_subgroup_core/syn_branch_syn_release",
                                "../all_tests_fixed_subgroup_core/syn_lock_step_release",
                                "../all_tests_fixed_subgroup_core/syn_subgroup_op_release",
                                "../all_tests_fixed_subgroup_core/syn_branch_syn_rwr",
                                "../all_tests_fixed_subgroup_core/syn_branch_syn_wrw",
                                "../all_tests_fixed_subgroup_core/syn_branch_syn_rr",
                                "../all_tests_fixed_subgroup_core/syn_lock_step_rwr",
                                "../all_tests_fixed_subgroup_core/syn_lock_step_wrw",
                                "../all_tests_fixed_subgroup_core/syn_lock_step_rr",
                                "../all_tests_fixed_subgroup_core/syn_subgroup_op_rwr",
                                "../all_tests_fixed_subgroup_core/syn_subgroup_op_wrw",
                                "../all_tests_fixed_subgroup_core/syn_subgroup_op_rr",
                            ]

    if sys.argv[1] == "core":
        directory_names = directory_names_core
    elif sys.argv[1] == "intel":
        directory_names = directory_names_intel
    elif sys.argv[1] == "intel_core":
        directory_names = directory_names_intel_core
    elif sys.argv[1] == "all":
        directory_names = directory_names
    for name in directory_names:
        command = "python3 amber_test_driver.py " + name + " 1"
        if args.android:
            command += " --android"
        if args.serial:
            command += f" --serial {args.serial}"
        if args.device:
            command += f" --device {args.device}"
        os.system(command)


if __name__ == "__main__":
    main()
