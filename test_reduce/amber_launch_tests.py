# -----------------------------------------------------------------------
# amber_launch_tests.py
# Authors: Hari Raval
# -----------------------------------------------------------------------
import sys
import os


# run the amber_test_driver.py script with all input directories available in Input_Files
def main():
    if len(sys.argv) != 1:
        print("ERROR: No command line arguments required to run this higher level script")
        exit(1)

    directory_names = ["../reduction_results/rtx_4070/syn_branch_syn",
                       "../reduction_results/rtx_4070/syn_branch_syn_relax",
                       "../reduction_results/rtx_4070/syn_branch_syn_release",
                       "../reduction_results/rtx_4070/syn_lock_step",
                       "../reduction_results/rtx_4070/syn_lock_step_relax",
                       "../reduction_results/rtx_4070/syn_lock_step_release",
                       "../reduction_results/rtx_4070/syn_subgroup_op",
                       "../reduction_results/rtx_4070/syn_subgroup_op_relax",
                       "../reduction_results/rtx_4070/syn_subgroup_op_release",
                       "../reduction_results/rtx_4070/syn_memory_converge",
                       "../reduction_results/rtx_4070/syn_memory_converge_atomic"]

    for name in directory_names:
        os.system("python3 amber_test_driver.py " + name + " 1")


if __name__ == "__main__":
    main()
