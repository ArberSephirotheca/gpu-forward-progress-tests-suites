# -----------------------------------------------------------------------
# amber_launch_tests.py
# Authors: Hari Raval
# -----------------------------------------------------------------------
import sys
import re
import os
import argparse
import subprocess
import pandas as pd

README_PATH = "../README.md"
RESULTS_SUMMARY_PATH = "../results_summary.csv"

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

def check_fails(directory):
    try:
        f = [f for f in os.listdir('results/' + directory) if re.match('simple_final_results.*csv', f)][0]
    except:
        print(f'no results csv found, skipping {"results/" + directory}')
        return True
    results = pd.read_csv(os.path.join('results', directory, f)).reset_index(drop=True)
    print(results['All Passed'].values[-1])
    failure = int(results['All Passed'].values[-1]) > 0
    return failure

def update_table(gpu, directory_name, failure, suite):
    print(f"Updating results for {'results/' + directory_name}")
    try:
        results = pd.read_csv(RESULTS_SUMMARY_PATH).reset_index(drop=True)
    except:
        results = pd.DataFrame(columns=['Device'] + [d.split('/')[-1] for d in SELECTION[suite]])
    if gpu not in results['Device'].values:
        results.loc[len(results)] = {'Device': gpu, directory_name: ('fail' if failure else 'pass')}
    else:
        results.loc[results['Device'] == gpu, directory_name] = 'fail' if failure else 'pass'
    print(results)
    results.to_csv(RESULTS_SUMMARY_PATH, index=False)
    marker = '#### RESULTS'
    with open(README_PATH, 'r') as old_readme, open('README.tmp', 'w') as temp_readme:
        for line in old_readme.readlines():
            if marker in line:
                temp_readme.write(line + '\n\n')
                break
            else:
                temp_readme.write(line)

        temp_readme.write(results.to_markdown(index=False, tablefmt="github"))
    os.replace('README.tmp', README_PATH)

def add_to_git(gpu, directory_name):
    out_dir = gpu + '/' + directory_name + '/'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    os.system('cp -r results/' + directory_name + '/* ' + gpu + '/' + directory_name + '/')
    try:
        os.system('git pull')
        os.system('git add ' + out_dir + '/*')
        os.system('git add ' + README_PATH)
        os.system('git add ' + RESULTS_SUMMARY_PATH)
        os.system('git commit -m "Update results for ' + gpu + ', ' + directory_name + '"')
        os.system('git push')

    except Exception as e:
        print(f"Error updating {directory_name} to git: {e}")

# run the amber_test_driver.py script with all input directories available in Input_Files
def main():
    p = argparse.ArgumentParser(description="Run Amber test suites")
    p.add_argument("suite", choices=SELECTION, help="which directory list to run")
    p.add_argument("--android", action="store_true", help="Android tests")
    p.add_argument("--serial", help="serial number of device (if more than one attached with adb)")
    p.add_argument("--device", help="vulkan device id (if more than 1 vulkan device available)")
    p.add_argument("--gpu", help="name of the device to be used in results summary", default=None)
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
        if not args.gpu:
            args.gpu = "unknown"
        try:
            update_table(args.gpu, name.split('/')[-1], check_fails(name.split('/')[-1]), args.suite)
            add_to_git(args.gpu, name.split('/')[-1])
        except Exception as e:
            print(f"Error updating results for {name}: {e}")
            continue


if __name__ == "__main__":
    main()
