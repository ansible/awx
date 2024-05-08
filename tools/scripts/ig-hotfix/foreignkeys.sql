DO $$
DECLARE
    topology text[] := ARRAY['main_instance', 'main_instancegroup', 'main_instancegroup_instances'];
    excluded text[] := ARRAY['main_instance', 'main_instancegroup', 'main_instancegroup_instances', 'main_organizationinstancegroupmembership', 'main_unifiedjobtemplateinstancegroupmembership', 'main_inventoryinstancegroupmembership'];
BEGIN
    CREATE TABLE tmp_fk_from AS (
        SELECT DISTINCT
            tc.table_name, 
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = ANY (excluded)
            AND NOT ccu.table_name = ANY (topology)
    );

    CREATE TABLE tmp_fk_into AS (
        SELECT DISTINCT
            tc.table_name, 
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = ANY (excluded)
            AND NOT tc.table_name = ANY (topology)
    );
END $$;

SELECT * FROM tmp_fk_from;
SELECT * FROM tmp_fk_into;

DROP TABLE tmp_fk_from;
DROP TABLE tmp_fk_into;
