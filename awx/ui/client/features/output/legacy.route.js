function LegacyRedirect ($http, $stateRegistry) {
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
        {
            name: 'workflowNodeRedirect',
            url: '/workflow_node_results/:id',
            redirectTo: (trans) => {
                // The workflow job viewer uses this route for playbook job nodes. The provided id
                // is used to lookup the corresponding unified job, which is then inspected to
                // determine if we need to redirect to a split (workflow) job or a playbook job.
                const { id } = trans.params();
                const endpoint = '/api/v2/unified_jobs/';

                return $http.get(endpoint, { params: { id } })
                    .then(({ data }) => {
                        const { results } = data;
                        const [obj] = results;

                        if (obj) {
                            if (obj.type === 'workflow_job') {
                                return { state: 'workflowResults', params: { id } };
                            } else if (obj.type === 'job') {
                                return { state: 'output', params: { type: 'playbook', id } };
                            } else if (obj.type === 'inventory_update') {
                                return { state: 'output', params: { type: 'inventory', id } };
                            } else if (obj.type === 'project_update') {
                                return { state: 'output', params: { type: 'project', id } };
                            }
                        }

                        return { state: 'jobs' };
                    })
                    .catch(() => ({ state: 'dashboard' }));
            }
        },
    ];

    routes.forEach(state => $stateRegistry.register(state));
}

LegacyRedirect.$inject = ['$http', '$stateRegistry'];

export default LegacyRedirect;
