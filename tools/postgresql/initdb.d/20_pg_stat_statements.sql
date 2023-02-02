create extension if not exists pg_stat_statements schema public;

revoke all on table pg_stat_statements from public;
grant select on table pg_stat_statements to current_user;

grant select on public.pg_stat_statements to db_monitor;
grant execute on function public.pg_stat_statements_reset to db_monitor;
