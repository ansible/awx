function HostEventService (
    Rest,
    ProcessErrors,
    GetBasePath,
    $rootScope
) {
    this.getUrl = (id, type, params) => {
        let url;
        if (type === 'playbook') {
            url = `${GetBasePath('jobs')}${id}/job_events/?${this.stringifyParams(params)}`;
        } else if (type === 'command') {
            url = `${GetBasePath('ad_hoc_commands')}${id}/events/?${this.stringifyParams(params)}`;
        }
        return url;
    };

    // GET events related to a job run
    // e.g.
    // ?event=playbook_on_stats
    // ?parent=206&event__startswith=runner&page_size=200&order=host_name,counter
    this.getRelatedJobEvents = (id, type, params) => {
        const url = this.getUrl(id, type, params);
        Rest.setUrl(url);
        return Rest.get()
            .then(response => response)
            .catch(({ data, status }) => {
                ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                    msg: `Call to ${url}. GET returned: ${status}` });
            });
    };

    this.stringifyParams = params => {
        function reduceFunction (result, value, key) {
            return `${result}${key}=${value}&`;
        }
        return _.reduce(params, reduceFunction, '');
    };

    // Generate a helper class for job_event statuses
    // the stack for which status to display is
    // unreachable > failed > changed > ok
    // uses the API's runner events and convenience properties .failed .changed to determine status.
    // see: job_event_callback.py for more filters to support
    this.processEventStatus = event => {
        const obj = {};
        if (event.event === 'runner_on_unreachable') {
            obj.class = 'HostEvent-status--unreachable';
            obj.status = 'unreachable';
        }
        // equiv to 'runner_on_error' && 'runner on failed'
        if (event.failed) {
            obj.class = 'HostEvent-status--failed';
            obj.status = 'failed';
        }
        // catch the changed case before ok, because both can be true
        if (event.changed) {
            obj.class = 'HostEvent-status--changed';
            obj.status = 'changed';
        }
        if (event.event === 'runner_on_ok' || event.event === 'runner_on_async_ok') {
            obj.class = 'HostEvent-status--ok';
            obj.status = 'ok';
        }
        if (event.event === 'runner_on_skipped') {
            obj.class = 'HostEvent-status--skipped';
            obj.status = 'skipped';
        }
        return obj;
    };
}

HostEventService.$inject = [
    'Rest',
    'ProcessErrors',
    'GetBasePath',
    '$rootScope'
];
export default HostEventService;
