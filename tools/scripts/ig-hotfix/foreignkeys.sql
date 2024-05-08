DO $$
DECLARE
    -- add table names here when they get excluded from main / included in topology dump
    topology text[] := ARRAY['main_instance', 'main_instancegroup', 'main_instancegroup_instances'];

    -- add table names here when they are handled by the special-case mapping
    mapping text[] := ARRAY['main_organizationinstancegroupmembership', 'main_unifiedjobtemplateinstancegroupmembership', 'main_inventoryinstancegroupmembership'];
BEGIN
    CREATE TABLE tmp_fk_from AS (
        SELECT DISTINCT
            tc.table_name, 
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = ANY (topology)
            AND NOT ccu.table_name = ANY (topology || mapping)
    );

    CREATE TABLE tmp_fk_into AS (
        SELECT DISTINCT
            tc.table_name, 
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = ANY (topology)
            AND NOT tc.table_name = ANY (topology || mapping)
    );
END $$;

SELECT * FROM tmp_fk_from;
SELECT * FROM tmp_fk_into;

DROP TABLE tmp_fk_from;
DROP TABLE tmp_fk_into;
