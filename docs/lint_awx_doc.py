#!/usr/bin/env python3

import sys
import yaml


def error(msg):
    print(f'[\033[91mERROR\033[0m] {msg}')
    sys.exit(1)


def warning(msg):
    print(f'[\033[93mWARNING\033[0m] {msg}')


def ok(msg):
    print(f'[\033[92mOK\033[0m] {msg}')


class AWXDocLinter:
    def __init__(self, filename):
        self.filename = filename
        with open(filename) as f:
            self.data = f.read()

    def lint(self):
        self.parse_metadata()
        self.has_tags()
        self.only_permitted_tags()

    def report(self, msg, success, verbose=False):
        if success and verbose:
            ok(f'[\033[95m{self.filename}\033[0m] {msg}')
        elif not success:
            error(f'[\033[95m{self.filename}\033[0m] {msg}')

    def parse_metadata(self):
        msg = 'File must start with metadata enclosed in ---'
        starts_with_metadata = self.data.startswith('---')
        self.report(msg, starts_with_metadata)

        if not starts_with_metadata:
            return

        try:
            # If it has metadata, then parse the lines between --- as YAML
            metadata = yaml.load(self.data.split('---')[1], Loader=yaml.FullLoader)
            self.metadata = metadata
        except yaml.YAMLError as e:
            self.report(f'Invalid YAML: {e}', False)
            return

    def has_tags(self):
        msg = 'Metadata must have tags'
        has_tags = 'tags' in self.metadata
        self.report(msg, has_tags)

    def only_permitted_tags(self):
        # Pull out permitted tags from mkdocs.yml
        with open('../mkdocs.yml') as f:
            mkdocs = yaml.safe_load(f)
            for plugin in mkdocs['plugins']:
                if type(plugin) == dict and 'tags' in plugin:
                    self.permitted_tags = plugin['tags']['tags_allowed']

        tags = self.metadata['tags']
        rejected_tags = [tag for tag in tags if tag not in self.permitted_tags]
        msg = f'Tags must be one of {self.permitted_tags} (found {rejected_tags})'
        self.report(msg, len(rejected_tags) == 0)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        error('Usage: lint_awx_doc.py <filename>')

    filename = sys.argv[1]
    if filename.endswith(('/_tags.md', '/index.md')):
        sys.exit(0)

    linter = AWXDocLinter(sys.argv[1])
    linter.lint()
