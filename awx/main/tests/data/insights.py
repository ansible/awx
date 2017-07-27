import json
import os 


dir_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_path, 'insights.json')) as data_file:
    TEST_INSIGHTS_PLANS = json.loads(data_file.read())

