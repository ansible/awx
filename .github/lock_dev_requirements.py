#!/usr/bin/env python

# Run by workflows/lock_dev_requirements.yml

import re

pinned_versions = {}
with open('./locked_requirements_dev.txt', 'r') as f:
    for line in f.read().splitlines():
        (package, version) = line.split('==')
        pinned_versions[package] = version

lines = []
errors = False
with open('./requirements_dev.txt', 'r') as f:
    for line in f.read().splitlines():
        comment = ''
        if '#' in line:
            package_version, comment = line.split('#', 2)
            comment = ' # {}'.format(comment)
            package_version = package_version.strip()
        else:
            package_version = line

        if not package_version or package_version.startswith('git'):
            # If the whole line was a comment or the the line was a git reference (which we can't find versions for)
            #   then append the whole line back to the list of lines.
            lines.append(line)
            continue

        package = re.split(r'[!=<>]+', package_version)[0]
        if package not in pinned_versions:
            print(f"I have failed you, the package {package} was not in the list of pinned versions.")
            errors = True
        else:
            lines.append(f'{package}=={pinned_versions[package]}{comment}')

if errors:
    import sys

    sys.exit(255)

with open('./requirements_dev.txt', 'w') as f:
    f.write("\n".join(lines))
