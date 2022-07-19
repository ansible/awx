#!/bin/bash

# Extract Strings from API & UI
make docker-compose-sources
docker-compose -f tools/docker-compose/_sources/docker-compose.yml run awx_1 make awx-link migrate po messages

# Move extracted Strings to Translation Directory
mv awx/locale/en-us/LC_MESSAGES/django.po translations/
mv awx/ui/src/locales/en/messages.po translations/

