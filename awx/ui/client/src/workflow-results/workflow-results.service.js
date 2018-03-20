/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['$q', 'Prompt', '$filter', 'Wait', 'Rest', '$state', 'ProcessErrors', 'WorkflowJobModel', '$interval', 'moment', function ($q, Prompt, $filter, Wait, Rest, $state, ProcessErrors, WorkflowJob, $interval, moment) {
    var val = {
        getCounts: function(workflowNodes){
            var nodeArr = [];
            workflowNodes.forEach(node => {
                if(node && node.summary_fields && node.summary_fields.job && node.summary_fields.job.status){
                    nodeArr.push(node.summary_fields.job.status);
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
                hdr: 'Delete Job',
                resourceName: `#${workflow.id} ` + $filter('sanitize')(workflow.name),
                body: `<div class='Prompt-bodyQuery'>
                        Are you sure you want to delete this workflow?
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
                                hdr: 'Error!',
                                msg: `Could not delete job.
                                    Returned status: ${status}`
                            });
                        });
                },
                actionText: 'DELETE'
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
                            hdr: 'Error!',
                            msg: `Could not cancel workflow.
                                Returned status: ${status}`
                        });
                    });
            };

            Prompt({
                hdr: 'Cancel Workflow',
                resourceName: `#${workflow.id} ${$filter('sanitize')(workflow.name)}`,
                body: `<div class='Prompt-bodyQuery'>
                        Are you sure you want to cancel this workflow job?
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
                                    hdr: 'Error!',
                                    msg: `Job has completed,
                                        unabled to be canceled.`
                                });
                            }
                        });
                },
                actionText: 'PROCEED'
            });
        },
        relaunchJob: function(scope) {
            const workflowJob = new WorkflowJob();

            workflowJob.postRelaunch({
                id: scope.workflow.id
            }).then((launchRes) => {
                $state.go('workflowResults', { id: launchRes.data.id }, { reload: true });
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
        },
    };
    return val;
}];
