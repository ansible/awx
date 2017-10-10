# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import base64
import collections
import difflib
import json
import os
import shutil

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# Tower
from awx import MODE
from awx.conf import settings_registry
from awx.conf.fields import empty, SkipField
from awx.conf.models import Setting
from awx.conf.utils import comment_assignments


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'category',
            nargs='*',
            type=str,
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help=_('Only show which settings would be commented/migrated.'),
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            dest='skip_errors',
            default=False,
            help=_('Skip over settings that would raise an error when commenting/migrating.'),
        )
        parser.add_argument(
            '--no-comment',
            action='store_true',
            dest='no_comment',
            default=False,
            help=_('Skip commenting out settings in files.'),
        )
        parser.add_argument(
            '--comment-only',
            action='store_true',
            dest='comment_only',
            default=False,
            help=_('Skip migrating and only comment out settings in files.'),
        )
        parser.add_argument(
            '--backup-suffix',
            dest='backup_suffix',
            default=now().strftime('.%Y%m%d%H%M%S'),
            help=_('Backup existing settings files with this suffix.'),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.dry_run = bool(options.get('dry_run', False))
        self.skip_errors = bool(options.get('skip_errors', False))
        self.no_comment = bool(options.get('no_comment', False))
        self.comment_only = bool(options.get('comment_only', False))
        self.backup_suffix = options.get('backup_suffix', '')
        self.categories = options.get('category', None) or ['all']
        self.style.HEADING = self.style.MIGRATE_HEADING
        self.style.LABEL = self.style.MIGRATE_LABEL
        self.style.OK = self.style.SQL_FIELD
        self.style.SKIP = self.style.WARNING
        self.style.VALUE = self.style.SQL_KEYWORD

        # Determine if any categories provided are invalid.
        category_slugs = []
        invalid_categories = []
        for category in self.categories:
            category_slug = slugify(category)
            if category_slug in settings_registry.get_registered_categories():
                if category_slug not in category_slugs:
                    category_slugs.append(category_slug)
            else:
                if category not in invalid_categories:
                    invalid_categories.append(category)
        if len(invalid_categories) == 1:
            raise CommandError('Invalid setting category: {}'.format(invalid_categories[0]))
        elif len(invalid_categories) > 1:
            raise CommandError('Invalid setting categories: {}'.format(', '.join(invalid_categories)))

        # Build a list of all settings to be migrated.
        registered_settings = []
        for category_slug in category_slugs:
            for registered_setting in settings_registry.get_registered_settings(category_slug=category_slug, read_only=False):
                if registered_setting not in registered_settings:
                    registered_settings.append(registered_setting)

        self._migrate_settings(registered_settings)

    def _get_settings_file_patterns(self):
        if MODE == 'development':
            return [
                '/etc/tower/settings.py',
                '/etc/tower/conf.d/*.py',
                os.path.join(os.path.dirname(__file__), '..', '..', '..', 'settings', 'local_*.py')
            ]
        else:
            return [
                os.environ.get('AWX_SETTINGS_FILE', '/etc/tower/settings.py'),
                os.path.join(os.environ.get('AWX_SETTINGS_DIR', '/etc/tower/conf.d/'), '*.py'),
            ]

    def _get_license_file(self):
        return os.environ.get('AWX_LICENSE_FILE', '/etc/tower/license')

    def _comment_license_file(self, dry_run=True):
        license_file = self._get_license_file()
        diff_lines = []
        if os.path.exists(license_file):
            try:
                raw_license_data = open(license_file).read()
                json.loads(raw_license_data)
            except Exception as e:
                raise CommandError('Error reading license from {0}: {1!r}'.format(license_file, e))
            if self.backup_suffix:
                backup_license_file = '{}{}'.format(license_file, self.backup_suffix)
            else:
                backup_license_file = '{}.old'.format(license_file)
            diff_lines = list(difflib.unified_diff(
                raw_license_data.splitlines(),
                [],
                fromfile=backup_license_file,
                tofile=license_file,
                lineterm='',
            ))
            if not dry_run:
                if self.backup_suffix:
                    shutil.copy2(license_file, backup_license_file)
                os.remove(license_file)
        return diff_lines

    def _get_local_settings_file(self):
        if MODE == 'development':
            static_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ui', 'static')
        else:
            static_root = settings.STATIC_ROOT
        return os.path.join(static_root, 'local_settings.json')

    def _comment_local_settings_file(self, dry_run=True):
        local_settings_file = self._get_local_settings_file()
        diff_lines = []
        if os.path.exists(local_settings_file):
            try:
                raw_local_settings_data = open(local_settings_file).read()
                json.loads(raw_local_settings_data)
            except Exception as e:
                if not self.skip_errors:
                    raise CommandError('Error reading local settings from {0}: {1!r}'.format(local_settings_file, e))
                return diff_lines
            if self.backup_suffix:
                backup_local_settings_file = '{}{}'.format(local_settings_file, self.backup_suffix)
            else:
                backup_local_settings_file = '{}.old'.format(local_settings_file)
            diff_lines = list(difflib.unified_diff(
                raw_local_settings_data.splitlines(),
                [],
                fromfile=backup_local_settings_file,
                tofile=local_settings_file,
                lineterm='',
            ))
            if not dry_run:
                if self.backup_suffix:
                    shutil.copy2(local_settings_file, backup_local_settings_file)
                os.remove(local_settings_file)
        return diff_lines

    def _get_custom_logo_file(self):
        if MODE == 'development':
            static_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ui', 'static')
        else:
            static_root = settings.STATIC_ROOT
        return os.path.join(static_root, 'assets', 'custom_console_logo.png')

    def _comment_custom_logo_file(self, dry_run=True):
        custom_logo_file = self._get_custom_logo_file()
        diff_lines = []
        if os.path.exists(custom_logo_file):
            try:
                raw_custom_logo_data = open(custom_logo_file).read()
            except Exception as e:
                if not self.skip_errors:
                    raise CommandError('Error reading custom logo from {0}: {1!r}'.format(custom_logo_file, e))
                return diff_lines
            if self.backup_suffix:
                backup_custom_logo_file = '{}{}'.format(custom_logo_file, self.backup_suffix)
            else:
                backup_custom_logo_file = '{}.old'.format(custom_logo_file)
            diff_lines = list(difflib.unified_diff(
                ['<PNG Image ({} bytes)>'.format(len(raw_custom_logo_data))],
                [],
                fromfile=backup_custom_logo_file,
                tofile=custom_logo_file,
                lineterm='',
            ))
            if not dry_run:
                if self.backup_suffix:
                    shutil.copy2(custom_logo_file, backup_custom_logo_file)
                os.remove(custom_logo_file)
        return diff_lines

    def _check_if_needs_comment(self, patterns, setting):
        files_to_comment = []
        # If any diffs are returned, this setting needs to be commented.
        diffs = comment_assignments(patterns, setting, dry_run=True)
        if setting == 'LICENSE':
            diffs.extend(self._comment_license_file(dry_run=True))
        elif setting == 'CUSTOM_LOGIN_INFO':
            diffs.extend(self._comment_local_settings_file(dry_run=True))
        elif setting == 'CUSTOM_LOGO':
            diffs.extend(self._comment_custom_logo_file(dry_run=True))
        for diff in diffs:
            for line in diff.splitlines():
                if line.startswith('+++ '):
                    files_to_comment.append(line[4:])
        return files_to_comment

    def _check_if_needs_migration(self, setting):
        # Check whether the current value differs from the default.
        default_value = settings.DEFAULTS_SNAPSHOT.get(setting, empty)
        if default_value is empty and setting != 'LICENSE':
            field = settings_registry.get_setting_field(setting, read_only=True)
            try:
                default_value = field.get_default()
            except SkipField:
                pass
        current_value = getattr(settings, setting, empty)
        if setting == 'CUSTOM_LOGIN_INFO' and current_value in {empty, ''}:
            local_settings_file = self._get_local_settings_file()
            try:
                if os.path.exists(local_settings_file):
                    local_settings = json.load(open(local_settings_file))
                    current_value = local_settings.get('custom_login_info', '')
            except Exception as e:
                if not self.skip_errors:
                    raise CommandError('Error reading custom login info from {0}: {1!r}'.format(local_settings_file, e))
        if setting == 'CUSTOM_LOGO' and current_value in {empty, ''}:
            custom_logo_file = self._get_custom_logo_file()
            try:
                if os.path.exists(custom_logo_file):
                    custom_logo_data = open(custom_logo_file).read()
                    if custom_logo_data:
                        current_value = 'data:image/png;base64,{}'.format(base64.b64encode(custom_logo_data))
                    else:
                        current_value = ''
            except Exception as e:
                if not self.skip_errors:
                    raise CommandError('Error reading custom logo from {0}: {1!r}'.format(custom_logo_file, e))
        if current_value != default_value:
            if current_value is empty:
                current_value = None
            return current_value
        return empty

    def _display_tbd(self, setting, files_to_comment, migrate_value, comment_error=None, migrate_error=None):
        if self.verbosity >= 1:
            if files_to_comment:
                if migrate_value is not empty:
                    action = 'Migrate + Comment'
                else:
                    action = 'Comment'
                if comment_error or migrate_error:
                    action = self.style.ERROR('{} (skipped)'.format(action))
                else:
                    action = self.style.OK(action)
                self.stdout.write('  {}: {}'.format(
                    self.style.LABEL(setting),
                    action,
                ))
                if self.verbosity >= 2:
                    if migrate_error:
                        self.stdout.write('    - Migrate value: {}'.format(
                            self.style.ERROR(migrate_error),
                        ))
                    elif migrate_value is not empty:
                        self.stdout.write('    - Migrate value: {}'.format(
                            self.style.VALUE(repr(migrate_value)),
                        ))
                    if comment_error:
                        self.stdout.write('    - Comment: {}'.format(
                            self.style.ERROR(comment_error),
                        ))
                    elif files_to_comment:
                        for file_to_comment in files_to_comment:
                            self.stdout.write('    - Comment in: {}'.format(
                                self.style.VALUE(file_to_comment),
                            ))
            else:
                if self.verbosity >= 2:
                    self.stdout.write('  {}: {}'.format(
                        self.style.LABEL(setting),
                        self.style.SKIP('No Migration'),
                    ))

    def _display_migrate(self, setting, action, display_value):
        if self.verbosity >= 1:
            if action == 'No Change':
                action = self.style.SKIP(action)
            else:
                action = self.style.OK(action)
            self.stdout.write('  {}: {}'.format(
                self.style.LABEL(setting),
                action,
            ))
            if self.verbosity >= 2:
                for line in display_value.splitlines():
                    self.stdout.write('    {}'.format(
                        self.style.VALUE(line),
                    ))

    def _display_diff_summary(self, filename, added, removed):
        self.stdout.write('  {} {}{} {}{}'.format(
            self.style.LABEL(filename),
            self.style.ERROR('-'),
            self.style.ERROR(int(removed)),
            self.style.OK('+'),
            self.style.OK(str(added)),
        ))

    def _display_comment(self, diffs):
        for diff in diffs:
            if self.verbosity >= 2:
                for line in diff.splitlines():
                    display_line = line
                    if line.startswith('--- ') or line.startswith('+++ '):
                        display_line = self.style.LABEL(line)
                    elif line.startswith('-'):
                        display_line = self.style.ERROR(line)
                    elif line.startswith('+'):
                        display_line = self.style.OK(line)
                    elif line.startswith('@@'):
                        display_line = self.style.VALUE(line)
                    if line.startswith('--- ') or line.startswith('+++ '):
                        self.stdout.write('  ' + display_line)
                    else:
                        self.stdout.write('    ' + display_line)
            elif self.verbosity >= 1:
                filename, lines_added, lines_removed = None, 0, 0
                for line in diff.splitlines():
                    if line.startswith('+++ '):
                        if filename:
                            self._display_diff_summary(filename, lines_added, lines_removed)
                        filename, lines_added, lines_removed = line[4:], 0, 0
                    elif line.startswith('+'):
                        lines_added += 1
                    elif line.startswith('-'):
                        lines_removed += 1
                if filename:
                    self._display_diff_summary(filename, lines_added, lines_removed)

    def _discover_settings(self, registered_settings):
        if self.verbosity >= 1:
            self.stdout.write(self.style.HEADING('Discovering settings to be migrated and commented:'))

        # Determine which settings need to be commented/migrated.
        to_migrate = collections.OrderedDict()
        to_comment = collections.OrderedDict()
        patterns = self._get_settings_file_patterns()

        for name in registered_settings:
            comment_error, migrate_error = None, None
            files_to_comment = []
            try:
                files_to_comment = self._check_if_needs_comment(patterns, name)
            except Exception as e:
                comment_error = 'Error commenting {0}: {1!r}'.format(name, e)
                if not self.skip_errors:
                    raise CommandError(comment_error)
            if files_to_comment:
                to_comment[name] = files_to_comment
            migrate_value = empty
            if files_to_comment:
                migrate_value = self._check_if_needs_migration(name)
                if migrate_value is not empty:
                    field = settings_registry.get_setting_field(name)
                    assert not field.read_only
                    try:
                        data = field.to_representation(migrate_value)
                        setting_value = field.run_validation(data)
                        db_value = field.to_representation(setting_value)
                        to_migrate[name] = db_value
                    except Exception as e:
                        to_comment.pop(name)
                        migrate_error = 'Unable to assign value {0!r} to setting "{1}: {2!s}".'.format(migrate_value, name, e)
                        if not self.skip_errors:
                            raise CommandError(migrate_error)
            self._display_tbd(name, files_to_comment, migrate_value, comment_error, migrate_error)
        if self.verbosity == 1 and not to_migrate and not to_comment:
            self.stdout.write('  No settings found to migrate or comment!')
        return (to_migrate, to_comment)

    def _migrate(self, to_migrate):
        if self.verbosity >= 1:
            if self.dry_run:
                self.stdout.write(self.style.HEADING('Migrating settings to database (dry-run):'))
            else:
                self.stdout.write(self.style.HEADING('Migrating settings to database:'))
            if not to_migrate:
                self.stdout.write('  No settings to migrate!')

        # Now migrate those settings to the database.
        for name, db_value in to_migrate.items():
            display_value = json.dumps(db_value, indent=4)
            setting = Setting.objects.filter(key=name, user__isnull=True).order_by('pk').first()
            action = 'No Change'
            if not setting:
                action = 'Migrated'
                if not self.dry_run:
                    Setting.objects.create(key=name, user=None, value=db_value)
            elif setting.value != db_value or type(setting.value) != type(db_value):
                action = 'Updated'
                if not self.dry_run:
                    setting.value = db_value
                    setting.save(update_fields=['value'])
            self._display_migrate(name, action, display_value)

    def _comment(self, to_comment):
        if self.verbosity >= 1:
            if bool(self.dry_run or self.no_comment):
                self.stdout.write(self.style.HEADING('Commenting settings in files (dry-run):'))
            else:
                self.stdout.write(self.style.HEADING('Commenting settings in files:'))
            if not to_comment:
                self.stdout.write('  No settings to comment!')

        # Now comment settings in settings files.
        if to_comment:
            to_comment_patterns = []
            license_file_to_comment = None
            local_settings_file_to_comment = None
            custom_logo_file_to_comment = None
            for files_to_comment in to_comment.values():
                for file_to_comment in files_to_comment:
                    if file_to_comment == self._get_license_file():
                        license_file_to_comment = file_to_comment
                    elif file_to_comment == self._get_local_settings_file():
                        local_settings_file_to_comment = file_to_comment
                    elif file_to_comment == self._get_custom_logo_file():
                        custom_logo_file_to_comment = file_to_comment
                    elif file_to_comment not in to_comment_patterns:
                        to_comment_patterns.append(file_to_comment)
            # Run once in dry-run mode to catch any errors from updating the files.
            diffs = comment_assignments(to_comment_patterns, to_comment.keys(), dry_run=True, backup_suffix=self.backup_suffix)
            # Then, if really updating, run again.
            if not self.dry_run and not self.no_comment:
                diffs = comment_assignments(to_comment_patterns, to_comment.keys(), dry_run=False, backup_suffix=self.backup_suffix)
                if license_file_to_comment:
                    diffs.extend(self._comment_license_file(dry_run=False))
                if local_settings_file_to_comment:
                    diffs.extend(self._comment_local_settings_file(dry_run=False))
                if custom_logo_file_to_comment:
                    diffs.extend(self._comment_custom_logo_file(dry_run=False))
            self._display_comment(diffs)

    def _migrate_settings(self, registered_settings):
        to_migrate, to_comment = self._discover_settings(registered_settings)

        if not bool(self.comment_only):
            self._migrate(to_migrate)
        self._comment(to_comment)
