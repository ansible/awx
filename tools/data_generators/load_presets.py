import os

preset = 'medium'

presets_filename = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'presets.tsv'))

with open(presets_filename) as f:
    text = f.read()

split_lines = [line.split('\t') for line in text.split('\n')]
keys = split_lines[0][1:]

try:
    col = keys.index(preset)
except ValueError:
    raise Exception('Preset %s data set not found, options are %s' % (preset, keys))

options = {cols[0]: cols[col+1] for cols in split_lines}

print ' text '
print text

print ' options '
print options
