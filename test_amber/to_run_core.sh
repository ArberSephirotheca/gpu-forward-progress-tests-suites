bash prep_dir.sh
python3 amber_launch_tests.py core
bash cleanup.sh
python3 summarize.py
