function LegacyRedirect ($stateRegistry) {
    const destination = 'output';
    const routes = [
        {
            name: 'legacyJobResult',
            url: '/jobs/:id?job_event_search',
            redirectTo: (trans) => {
                const {
                    id,
                    job_event_search // eslint-disable-line camelcase
                } = trans.params();

                return { state: destination, params: { type: 'playbook', id, job_event_search } };
            }
        },
        {
            name: 'legacyAdHocJobStdout',
            url: '/ad_hoc_commands/:id',
            redirectTo: (trans) => {
                const { id } = trans.params();
                return { state: destination, params: { type: 'command', id } };
            }
        },
        {
            name: 'legacyInventorySyncStdout',
            url: '/inventory_sync/:id',
            redirectTo: (trans) => {
                const { id } = trans.params();
                return { state: destination, params: { type: 'inventory', id } };
            }
        },
        {
            name: 'legacyManagementJobStdout',
            url: '/management_jobs/:id',
            redirectTo: (trans) => {
                const { id } = trans.params();
                return { state: destination, params: { type: 'system', id } };
            }
        },
        {
            name: 'legacyScmUpdateStdout',
            url: '/scm_update/:id',
            redirectTo: (trans) => {
                const { id } = trans.params();
                return { state: destination, params: { type: 'project', id } };
            }
        },
        {
            name: 'legacySchedulesList',
            url: '/jobs/schedules?schedule_search',
            redirectTo: (trans) => {
                const {
                    schedule_search // eslint-disable-line camelcase
                } = trans.params();
                return { state: 'schedules', params: { schedule_search } };
            }
        },
        {
            name: 'legacySchedule',
            url: '/jobs/schedules/:schedule_id?schedule_search',
            redirectTo: (trans) => {
                const {
                    schedule_id, // eslint-disable-line camelcase
                    schedule_search // eslint-disable-line camelcase
                } = trans.params();
                return { state: 'schedules.edit', params: { schedule_id, schedule_search } };
            }
        },
    ];

    routes.forEach(state => $stateRegistry.register(state));
}

LegacyRedirect.$inject = ['$stateRegistry'];

export default LegacyRedirect;
