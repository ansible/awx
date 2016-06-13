export default
    ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', function($rootScope, Rest, GetBasePath, ProcessErrors){
        return {
        stringifyParams: function(params){
            return  _.reduce(params, (result, value, key) => {
                return result + key + '=' + value + '&';
            }, '');
        },

        // the the API passes through Ansible's event_data response
        // we need to massage away the verbose & redundant stdout/stderr properties
        processJson: function(data){
            // configure fields to ignore
            var ignored = [
            'type',
            'event_data',
            'related',
            'summary_fields',
            'url',
            'ansible_facts',
            ];
            // remove ignored properties
            var result = _.chain(data).cloneDeep().forEach(function(value, key, collection){
                if (ignored.indexOf(key) > -1){
                    delete collection[key];
                }
            }).value();
            return result;
        },
        // Return Ansible's passed-through response msg on a job_event
        processEventMsg: function(event){
            return typeof event.event_data.res === 'object' ? event.event_data.res.msg : event.event_data.res;
        },
        // Return only Ansible's passed-through response item on a job_event
        processEventItem: function(event){
            try{
                var item = event.event_data.res.item;
                return typeof item === 'object' ? JSON.stringify(item) : item;
            }
            catch(err){return;}
        },
        // Generate a helper class for job_event statuses
        // the stack for which status to display is
        // unreachable > failed > changed > ok
        // uses the API's runner events and convenience properties .failed .changed to determine status.
        // see: job_event_callback.py for more filters to support
        processEventStatus: function(event){
            if (event.event === 'runner_on_unreachable'){
                return {
                    class: 'HostEvents-status--unreachable',
                    status: 'unreachable'
                };
            }
            // equiv to 'runner_on_error' && 'runner on failed'
            if (event.failed){
                return {
                    class: 'HostEvents-status--failed',
                    status: 'failed'
                };
            }
            // catch the changed case before ok, because both can be true
            if (event.changed){
                return {
                    class: 'HostEvents-status--changed',
                    status: 'changed'
                };
            }
            if (event.event === 'runner_on_ok' || event.event === 'runner_on_async_ok'){
                return {
                    class: 'HostEvents-status--ok',
                    status: 'ok'
                };
            }
            if (event.event === 'runner_on_skipped'){
                return {
                    class: 'HostEvents-status--skipped',
                    status: 'skipped'
                };
            }
        },
        // Consumes a response from this.getRelatedJobEvents(id, params)
        // returns an array for view logic to iterate over to build host result rows
        processHostEvents: function(data){
            var self = this;
            var results = [];
            data.forEach(function(event){
                if (event.event !== 'runner_on_no_hosts'){
                    var status = self.processEventStatus(event);
                    var msg = self.processEventMsg(event);
                    var item = self.processEventItem(event);
                    results.push({
                        id: event.id,
                        status: status.status,
                        status_text: _.head(status.status).toUpperCase() + _.tail(status.status),
                        host_id: event.host,
                        task_id: event.parent,
                        name: event.event_data.host,
                        created: event.created,
                        msg: typeof msg === 'undefined' ? undefined : msg,
                        item: typeof item === 'undefined' ? undefined : item
                    });
                }
            });
            return results;
        },
        // GET events related to a job run
        // e.g.
        // ?event=playbook_on_stats
        // ?parent=206&event__startswith=runner&page_size=200&order=host_name,counter
        getRelatedJobEvents: function(id, params){
            var url = GetBasePath('jobs');
            url = url + id + '/job_events/?' + this.stringifyParams(params);
            Rest.setUrl(url);
            return Rest.get()
                .success(function(data){
                    return data;
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        },
        getJobEventChildren: function(id){
            var url = GetBasePath('job_events');
            url = url + id + '/children/';
            Rest.setUrl(url);
            return Rest.get()
                .success(function(data){
                    return data;
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        },
        // GET job host summaries related to a job run
        // e.g. ?page_size=200&order=host_name
        getJobHostSummaries: function(id, params){
            var url = GetBasePath('jobs');
            url = url + id + '/job_host_summaries/?' + this.stringifyParams(params);
            Rest.setUrl(url);
            return Rest.get()
                .success(function(data){
                    return data;
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        },
        // GET job plays related to a job run
        // e.g. ?page_size=200
        getJobPlays: function(id, params){
            var url = GetBasePath('jobs');
            url = url + id + '/job_plays/?' + this.stringifyParams(params);
            Rest.setUrl(url);
            return Rest.get()
                .success(function(data){
                    return data;
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        },
        getJobTasks: function(id, params){
            var url = GetBasePath('jobs');
            url = url + id + '/job_tasks/?' + this.stringifyParams(params);
            Rest.setUrl(url);
            return Rest.get()
                .success(function(data){
                    return data;
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        },
        getJob: function(params){
            var url = GetBasePath('unified_jobs') + '?' + this.stringifyParams(params);
            Rest.setUrl(url);
            return Rest.get()
                .success(function(data){
                    return data;
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        },
        // GET next set of paginated results
        // expects 'next' param returned by the API e.g.
        // "/api/v1/jobs/51/job_plays/?order_by=id&page=2&page_size=1"
        getNextPage: function(url){
            Rest.setUrl(url);
            return Rest.get()
                .success(function(data){
                    return data;
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
        }
        };
    }];
