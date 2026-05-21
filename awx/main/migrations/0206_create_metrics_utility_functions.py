from django.db import migrations

from ._sqlite_helper import dbawaremigrations

CREATE_FUNCTIONS_SQL = """
    CREATE OR REPLACE FUNCTION metrics_utility_parse_yaml_field(
        str text,
        field text
    )
    RETURNS text AS
    $$
    DECLARE
        line_re text;
        field_re text;
    BEGIN
        field_re := ' *[:=] *(.+?) *$';
        line_re := '(?n)^' || field || field_re;
        RETURN trim(both '"' from substring(str from line_re));
    END;
    $$
    LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION metrics_utility_is_valid_json(p_json text)
        RETURNS boolean
    AS
    $$
    BEGIN
        RETURN (p_json::json IS NOT NULL);
    EXCEPTION
        WHEN others
        THEN RETURN false;
    END;
    $$
    LANGUAGE plpgsql;

    GRANT EXECUTE ON FUNCTION metrics_utility_parse_yaml_field(text, text) TO PUBLIC;
    GRANT EXECUTE ON FUNCTION metrics_utility_is_valid_json(text) TO PUBLIC;
"""

DROP_FUNCTIONS_SQL = """
    DROP FUNCTION IF EXISTS metrics_utility_parse_yaml_field(text, text);
    DROP FUNCTION IF EXISTS metrics_utility_is_valid_json(text);
"""


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        dbawaremigrations.RunSQL(
            sql=CREATE_FUNCTIONS_SQL,
            reverse_sql=DROP_FUNCTIONS_SQL,
            sqlite_sql=dbawaremigrations.RunSQL.noop,
            sqlite_reverse_sql=dbawaremigrations.RunSQL.noop,
        ),
    ]
