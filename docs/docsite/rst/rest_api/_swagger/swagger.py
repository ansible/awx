import io
import json
import os

import jinja2
import pkg_resources
import yaml

from sphinx.util.osutil import copyfile, ensuredir

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'swagger.json'), 'r', encoding='utf-8') as f:
    spec = json.load(f)
with io.open(os.path.join(here, 'tags.yml'), 'r', encoding='utf-8') as f:
    tags = yaml.load(f.read(), Loader=yaml.FullLoader)


def add_spec(app, pagename, templatename, context, doctree):
    if pagename == 'rest_api/api_ref':
        # Write tags in the order we want them sorted
        for category in tags.get('categories', []):
            tag = {'name': category['name']}
            if 'description' in category:
                tag['description'] = category['description']
            spec.setdefault('tags', []).append(tag)

        context['body'] = context['body'].replace('{{SPEC}}', json.dumps(spec))


def assets(app, exception):
    for asset in os.listdir(here):
        if asset == '__pycache__':
            continue

        _, extension = os.path.splitext(asset)
        if extension in ('py', 'pyc'):
            continue
        if not exception and os.path.exists(
            os.path.join(app.outdir, '_static')
        ):
            copyfile(
                os.path.join(here, asset),
                os.path.join(app.outdir, '_static', asset))


def setup(app):
    app.add_config_value('swagger', [], 'html')
    app.connect('html-page-context', add_spec)
    app.connect('build-finished', assets)
    return {'version': 1.0, 'parallel_read_safe': True}
