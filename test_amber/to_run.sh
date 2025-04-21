bash prep_dir.sh
python3 amber_launch_tests.py all
bash cleanup.sh
python3 summarize.py
