bash prep_dir.sh
python3 amber_launch_tests.py intel 
bash cleanup.sh
python3 summarize.py
