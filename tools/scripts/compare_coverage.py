#!/usr/bin/env python

from git import Repo
from sys import exit, argv
from xml.etree import ElementTree as ET


def percentage(number):
    return "{}%".format(round(float(number) * 100, 2))


def print_table(headers, data):
    # Make the smallest side of the column the length of the header
    longest = []
    for header in headers:
        longest.append(len(header))

    # Search the data to see if any field is longer than the longest header
    max_data_array_length = 1
    for entry in table:
        for index in range(0, len(longest)):
            value = entry[index]
            if isinstance(value, list):
                # if this item is an array we have to search down through the array
                max_data_array_length = len(entry)
                for line in entry[index]:
                    if len(line) > longest[index]:
                        longest[index] = len(line)
            else:
                if len(value) > longest[index]:
                    longest[index] = len(value)

    # Make a separator line based on the longest fields and print it
    separator_headers = []
    for max_column_size in longest:
        separator_headers.append("-" * (max_column_size + 2))
    separator_line = "".join(
        [
            "|",
            "|".join(separator_headers),
            "|",
        ]
    )

    print(separator_line)

    # Create and print header line followed by a separator
    header_fields = []
    for index in range(0, len(headers)):
        header_fields.append(headers[index] + " " * (longest[index] + 1 - len(headers[index])))
    print(
        "".join(
            [
                "| ",
                "| ".join(header_fields),
                "|",
            ]
        )
    )
    print(separator_line)

    for row in table:
        for array_index in range(0, max_data_array_length):
            cells = []
            row_has_content = False
            for cell_index in range(0, len(headers)):
                cell_value = None
                if isinstance(row[cell_index], list):
                    try:
                        cell_value = row[cell_index][array_index]
                    except:
                        pass
                else:
                    if array_index == 0:
                        cell_value = row[cell_index]

                if cell_value:
                    cells.append(cell_value + " " * (longest[cell_index] + 1 - len(cell_value)))
                    row_has_content = True
                else:
                    cells.append(" " * (longest[cell_index] + 1))

            if row_has_content:
                print(
                    "".join(
                        [
                            "| ",
                            "| ".join(cells),
                            "|",
                        ]
                    )
                )
        print(separator_line)

    if table == []:
        print(separator_line)


merge_point = 'devel'
try:
    merge_point = argv[1]
except Exception:
    pass

# Get the files different from head to now from git
run_test = False
repo = Repo(".", search_parent_directories=True)
changed_files = [item.a_path for item in repo.index.diff(merge_point)]
for file in changed_files:
    if file.startswith('awx/'):
        run_test = True

if not run_test:
    print("None of the files in the awx/ directory changed, no need for this test")
    exit(0)

# Read the current coverage
try:
    current_tree = ET.parse('reports/current.xml')
    current_root = current_tree.getroot()
except Exception as e:
    print(f"Failed to parse current coverage: {e}")
    exit(255)

# Read the devel coverage
try:
    devel_tree = ET.parse('reports/devel.xml')
    devel_root = devel_tree.getroot()
except Exception as e:
    print(f"Failed to parse the devel coverage: {e}")
    exit(255)

results = {}
fatal_xml_errors = 0
for file_name in changed_files:
    results[file_name] = {'current': None, 'devel': None}
    # In the report the leading /awx will be missing
    report_file_name = file_name.replace("awx/", "")

    summary_node = current_root.findall(f"packages/package/classes/class[@filename='{report_file_name}']")
    if len(summary_node) == 1:
        results[file_name]['current'] = summary_node[0].attrib
    elif len(summary_node) > 1:
        # We shouldn't ever get here but CYA, am I right?
        print(f"Error: file {file_name} had more than one match!")
        fatal_xml_errors = fatal_xml_errors + 1

    summary_node = devel_root.findall(f"packages/package/classes/class[@filename='{report_file_name}']")
    if len(summary_node) == 1:
        results[file_name]['devel'] = summary_node[0].attrib
    elif len(summary_node) > 1:
        # We shouldn't ever get here but CYA, am I right?
        print(f"Error: file {file_name} had more than one match!")
        fatal_xml_errors = fatal_xml_errors + 1

if fatal_xml_errors:
    print("Failed to process one or more file, see messages above")
    exit(254)


# We are attempting to make table rows like this, here we will parse the collected data
# File Name    File State  Coverage Level change                Coverage Status
#  <filename>   New          line-rage <old> <new> <change>      OK
#               Deleted      complexity <old> <new> <change>     Failed: new files should be 80%
#               Untested     branch-rage <old> <new> <change>    Failed: coverage decreased
#               Changed                                          Great, coverage increased
#
test_failed = False
table = []
for file_name in changed_files:

    file_state = 'Changed'
    coverage_lines = ['N/A']
    coverage_status = "OK"

    # Figure out the file state
    if not results[file_name]['current'] and not results[file_name]['devel']:
        file_state = 'Untested'
    elif results[file_name]['current'] and not results[file_name]['devel']:
        file_state = 'New'
    elif not results[file_name]['current'] and results[file_name]['devel']:
        file_state = 'Deleted'

    # Figure out the coverage level change
    if file_state == 'New':
        coverage_lines = []
        for entry in ['complexity', 'line-rate', 'branch-rate']:
            coverage_lines.append(f"{entry}: {percentage(results[file_name]['current'][entry])}")
        if float(results[file_name]['current']['line-rate']) < 0.8:
            coverage_status = "Failed: New files should have 80% coverage"
            test_failed = True
    elif file_state == 'Changed':
        coverage_status = "OK, no change"
        coverage_lines = []
        failed_message = 'Failed: coverage decreased'
        for entry in ['complexity', 'line-rate', 'branch-rate']:
            old_value = results[file_name]['devel'][entry]
            new_value = results[file_name]['current'][entry]
            delta = float(new_value) - float(old_value)
            if delta > 0 and coverage_status != failed_message:
                # If our delta is positive and no other delta failed us already, we are great!
                coverage_status = 'Great: coverage increased'
            elif delta < 0:
                # If our delta is ever smaller, we failed
                coverage_status = failed_message
                test_failed = True
            coverage_lines.append(f"{entry}: ({percentage(old_value)}) ({percentage(new_value)}) ({percentage(delta)})")

    table.append([file_name, file_state, coverage_lines, coverage_status])


# Finally, display the data in a pretty table
print_table(['File Name', 'File State', 'Coverage Level', 'Coverage Status'], table)


print('')
print('')
# Compute summary table
table = []
fields = ['lines-valid', 'lines-covered', 'line-rate', 'branches-valid', 'branches-covered', 'branch-rate', 'complexity']
for field in fields:
    devel_value = devel_root.attrib[field]
    current_value = current_root.attrib[field]
    if field.endswith('-rate'):
        delta = percentage(float(current_value) - float(devel_value))
        devel_value = percentage(devel_value)
        current_value = percentage(current_value)
    else:
        delta = f'{int(current_value) - int(devel_value)}'
    row = [field, devel_value, current_value, delta]
    table.append(row)

print_table(['Stat', 'Devel', 'Current Branch', 'Delta'], table)


if test_failed:
    exit(1)

# Sample data from an xml file:
#
# <coverage version="6.5.0" timestamp="1673392996426" lines-valid="53459" lines-covered="43190" line-rate="0.8079" branches-valid="14361" branches-covered="9181" branch-rate="0.6393" complexity="0">
#        <!-- Generated by coverage.py: https://coverage.readthedocs.io -->
#        <!-- Based on https://raw.githubusercontent.com/cobertura/web/master/htdocs/xml/coverage-04.dtd -->
#        <sources>
#                <source>/awx_devel/awx</source>
#        </sources>
#        <packages>
#                <package name="." line-rate="0.247" branch-rate="0.04545" complexity="0">
#                        <classes>
#                                <class name="__init__.py" filename="__init__.py" complexity="0" line-rate="0.2636" branch-rate="0.03333">
