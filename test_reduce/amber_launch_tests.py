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

    directory_names = ["../reduction_results/failed_variants/rtx_4070/syn_memory_converge_ww",
                       "../reduction_results/failed_variants/rtx_4070/syn_memory_converge_ra",]

    for name in directory_names:
        os.system("python3 amber_test_driver.py " + name + " 1")


if __name__ == "__main__":
    main()
