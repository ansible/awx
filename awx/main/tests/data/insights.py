import json
import os 


dir_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_path, 'insights_hosts.json')) as data_file:
    TEST_INSIGHTS_HOSTS = json.load(data_file)

with open(os.path.join(dir_path, 'insights.json')) as data_file:
    TEST_INSIGHTS_PLANS = json.load(data_file)

with open(os.path.join(dir_path, 'insights_remediations.json')) as data_file:
    TEST_INSIGHTS_REMEDIATIONS = json.load(data_file)['data']
