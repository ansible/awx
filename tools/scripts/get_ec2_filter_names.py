#!/usr/bin/env python

import json
import sys
import requests
from bs4 import BeautifulSoup

response = requests.get('http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-DescribeInstances.html')
soup = BeautifulSoup(response.text)

section_h3 = soup.find(id='query-DescribeInstances-filters')
section_div = section_h3.find_parent('div', attrs={'class': 'section'})

filter_names = []
for term in section_div.select('div.variablelist dt span.term'):
    filter_name = term.get_text()
    if not filter_name.startswith('tag:'):
        filter_names.append(filter_name)
filter_names.sort()

json.dump(filter_names, sys.stdout, indent=4)
