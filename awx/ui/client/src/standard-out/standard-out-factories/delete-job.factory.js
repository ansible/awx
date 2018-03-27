export default
function DeleteJob($state, Find, Rest, Wait, ProcessErrors, Prompt, Alert,
    $filter, i18n) {
    return function(params) {
        var scope = params.scope,
            id = params.id,
            job = params.job,
            callback = params.callback,
            action, jobs, url, action_label, hdr;

        if (!job) {
            if (scope.completed_jobs) {
                jobs = scope.completed_jobs;
            }
            else if (scope.running_jobs) {
                jobs = scope.running_jobs;
            }
            else if (scope.queued_jobs) {
                jobs = scope.queued_jobs;
            }
            else if (scope.all_jobs) {
                jobs = scope.all_jobs;
            }
            else if (scope.jobs) {
                jobs = scope.jobs;
            }
            job = Find({list: jobs, key: 'id', val: id });
        }

        if (job.status === 'pending' || job.status === 'running' || job.status === 'waiting') {
            url = job.related.cancel;
            action_label = 'cancel';
            hdr = i18n._('Cancel');
        } else {
            url = job.url;
            action_label = 'delete';
            hdr = i18n._('Delete');
        }

        action = function () {
            Wait('start');
            Rest.setUrl(url);
            if (action_label === 'cancel') {
                Rest.post()
                    .then(() => {
                        $('#prompt-modal').modal('hide');
                        if (callback) {
                            scope.$emit(callback, action_label);
                        }
                        else {
                            $state.reload();
                            Wait('stop');
                        }
                    })
                    .catch(({obj, status}) => {
                        Wait('stop');
                        $('#prompt-modal').modal('hide');
                        if (status === 403) {
                            Alert('Error', obj.detail);
                        }
                        // Ignore the error. The job most likely already finished.
                        // ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                        //    ' failed. POST returned status: ' + status });
                    });
            } else {
                Rest.destroy()
                    .then(() => {
                        $('#prompt-modal').modal('hide');
                        if (callback) {
                            scope.$emit(callback, action_label);
                        }
                        else {
                            let reloadListStateParams = null;

                            if(scope.jobs.length === 1 && $state.params.job_search && !_.isEmpty($state.params.job_search.page) && $state.params.job_search.page !== '1') {
                                reloadListStateParams = _.cloneDeep($state.params);
                                reloadListStateParams.job_search.page = (parseInt(reloadListStateParams.job_search.page)-1).toString();
                            }

                            $state.go('.', reloadListStateParams, {reload: true});
                            Wait('stop');
                        }
                    })
                    .catch(({obj, status}) => {
                        Wait('stop');
                        $('#prompt-modal').modal('hide');
                        if (status === 403) {
                            Alert('Error', obj.detail);
                        }
                        // Ignore the error. The job most likely already finished.
                        //ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                        //    ' failed. DELETE returned status: ' + status });
                    });
            }
        };

        if (scope.removeCancelNotAllowed) {
            scope.removeCancelNotAllowed();
        }
        scope.removeCancelNotAllowed = scope.$on('CancelNotAllowed', function() {
            Wait('stop');
            Alert('Job Completed', 'The request to cancel the job could not be submitted. The job already completed.', 'alert-info');
        });

        if (scope.removeCancelJob) {
            scope.removeCancelJob();
        }
        scope.removeCancelJob = scope.$on('CancelJob', function() {
            var cancelBody = "<div class=\"Prompt-bodyQuery\">" + i18n._("Are you sure you want to submit the request to cancel this job?") + "</div>";
            var deleteBody = "<div class=\"Prompt-bodyQuery\">" + i18n._("Are you sure you want to delete this job?") + "</div>";
            Prompt({
                hdr: hdr,
                resourceName: `#${job.id} ` + $filter('sanitize')(job.name),
                body: (action_label === 'cancel' || job.status === 'new') ? cancelBody : deleteBody,
                action: action,
                actionText: (action_label === 'cancel' || job.status === 'new') ? i18n._("OK") : i18n._("DELETE")
            });
        });

        if (action_label === 'cancel') {
            Rest.setUrl(url);
            Rest.get()
                .then(({data}) => {
                    if (data.can_cancel) {
                        scope.$emit('CancelJob');
                    }
                    else {
                        scope.$emit('CancelNotAllowed');
                    }
                })
                .catch(({data, status}) => {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Call to ' + url +
                        ' failed. GET returned: ' + status });
                });
        }
        else {
            scope.$emit('CancelJob');
        }
    };
}

DeleteJob.$inject =
[   '$state', 'Find', 'Rest', 'Wait',
    'ProcessErrors', 'Prompt', 'Alert', '$filter', 'i18n'
];
