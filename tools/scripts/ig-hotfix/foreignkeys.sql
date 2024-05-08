SELECT DISTINCT
    tc.table_name, 
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND (tc.table_name IN ('main_instance', 'main_instancegroup', 'main_instancegroup_instances')
         OR ccu.table_name IN ('main_instance', 'main_instancegroup', 'main_instancegroup_instances'));
