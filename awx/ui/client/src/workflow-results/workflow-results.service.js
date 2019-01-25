/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['i18n', 'Prompt', '$filter', 'Wait', 'Rest', '$state', 'ProcessErrors', 'WorkflowJobModel', '$interval', 'moment', 'ComponentsStrings', function (i18n, Prompt, $filter, Wait, Rest, $state, ProcessErrors, WorkflowJob, $interval, moment, strings) {
    var val = {
        getCounts: function(workflowNodes){
            var nodeArr = [];
            workflowNodes.forEach(node => {
                if(node && node.summary_fields && node.summary_fields.job && node.summary_fields.job.status){
                    nodeArr.push(node.summary_fields.job.status);
                } else if (_.has(node, 'job.status')) {
                    nodeArr.push(node.job.status);
                }
            });
            // use the workflow nodes data populate above to get the count
            var count = {
                successful : _.filter(nodeArr, function(o){
                    return o === "successful";
                }),
                failed : _.filter(nodeArr, function(o){
                    return o === "failed" || o === "error" || o === "canceled";
                })
            };

            // turn the count into an actual count, rather than a list of
            // statuses
            Object.keys(count).forEach(key => {
                count[key] = count[key].length;
            });

            return count;
        },
        deleteJob: function(workflow) {
            Prompt({
                hdr: i18n._('Delete Job'),
                resourceName: `#${workflow.id} ` + $filter('sanitize')(workflow.name),
                body: `<div class='Prompt-bodyQuery'>
                        ${i18n._('Are you sure you want to delete this workflow?')}
                    </div>`,
                action: function() {
                    Wait('start');
                    Rest.setUrl(workflow.url);
                    Rest.destroy()
                        .then(() => {
                            Wait('stop');
                            $('#prompt-modal').modal('hide');
                            $state.go('jobs');
                        })
                        .catch(({obj, status}) => {
                            Wait('stop');
                            $('#prompt-modal').modal('hide');
                            ProcessErrors(null, obj, status, null, {
                                hdr: i18n._('Error!'),
                                msg: `${i18n._('Could not delete job.  Returned status: ' + status)}`
                            });
                        });
                },
                actionText: i18n._('DELETE')
            });
        },
        cancelJob: function(workflow) {
            var doCancel = function() {
                Rest.setUrl(workflow.url + 'cancel');
                Rest.post({})
                    .then(() => {
                        Wait('stop');
                        $('#prompt-modal').modal('hide');
                    })
                    .catch(({obj, status}) => {
                        Wait('stop');
                        $('#prompt-modal').modal('hide');
                        ProcessErrors(null, obj, status, null, {
                            hdr: i18n._('Error!'),
                            msg: `${i18n._('Could not cancel workflow.  Returned status: ' + status)}`
                        });
                    });
            };

            Prompt({
                hdr: i18n._('Cancel Workflow'),
                resourceName: `#${workflow.id} ${$filter('sanitize')(workflow.name)}`,
                body: `<div class='Prompt-bodyQuery'>
                        ${i18n._('Are you sure you want to cancel this workflow job?')}
                    </div>`,
                action: function() {
                    Wait('start');
                    Rest.setUrl(workflow.url + 'cancel');
                    Rest.get()
                        .then(({data}) => {
                            if (data.can_cancel === true) {
                                doCancel();
                            } else {
                                $('#prompt-modal').modal('hide');
                                ProcessErrors(null, data, null, null, {
                                    hdr: i18n._('Error!'),
                                    msg: `${i18n._('Job has completed.  Unable to be canceled.')}`
                                });
                            }
                        });
                },
                actionText: i18n._('PROCEED')
            });
        },
        relaunchJob: function(scope) {
            const workflowJob = new WorkflowJob();

            workflowJob.postRelaunch({
                id: scope.workflow.id
            }).then((launchRes) => {
                $state.go('workflowResults', { id: launchRes.data.id }, { reload: true });
            }).catch(({ data, status, config }) => {
                ProcessErrors(scope, data, status, null, {
                    hdr: strings.get('error.HEADER'),
                    msg: strings.get('error.CALL', { path: `${config.url}`, status })
                });
            });
        },
        createOneSecondTimer: function(startTime, fn) {
            return $interval(function(){
                fn(moment().diff(moment(startTime), 'seconds'));
            }, 1000);
        },
        destroyTimer: function(timer) {
            if (timer !== null) {
                $interval.cancel(timer);
                timer = null;
                return true;
            }
            return false;
        }
    };
    return val;
}];
