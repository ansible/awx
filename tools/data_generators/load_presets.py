import os

presets_filename = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'presets.tsv'))

with open(presets_filename) as f:
    r = f.read()

print r

lines = r.split('\n')
keys = lines[0].split('\t')[1:]

preset = 'medium'

col = None
for i, key in enumerate(keys):
    if key == preset:
        col = i
        break

if col is None:
    raise Exception('Preset %s data set not found, options are %s' % (preset, keys))


options = {}

for line in lines[1:]:
    cols = line.split('\t')
    options[cols[0]] = cols[i+1]

print ' options '
print options
