"""
API versioning file; we can tell what kind of migrations things are
by what class they inherit from (if none, it's a v1).
"""

from south.utils import ask_for_it_by_name

class BaseMigration(object):
    
    def gf(self, field_name):
        "Gets a field by absolute reference."
        return ask_for_it_by_name(field_name)

class SchemaMigration(BaseMigration):
    pass

class DataMigration(BaseMigration):
    # Data migrations shouldn't be dry-run
    no_dry_run = True
