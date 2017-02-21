/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['$q', 'Prompt', '$filter', 'Wait', 'Rest', '$state', 'ProcessErrors', 'InitiatePlaybookRun', '$interval', 'moment', function ($q, Prompt, $filter, Wait, Rest, $state, ProcessErrors, InitiatePlaybookRun, $interval, moment) {
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
                body: `<div class='Prompt-bodyQuery'>
                        Are you sure you want to delete the workflow below?
                    </div>
                    <div class='Prompt-bodyTarget'>
                        #${workflow.id} ${$filter('sanitize')(workflow.name)}
                    </div>`,
                action: function() {
                    Wait('start');
                    Rest.setUrl(workflow.url);
                    Rest.destroy()
                        .success(function() {
                            Wait('stop');
                            $('#prompt-modal').modal('hide');
                            $state.go('jobs');
                        })
                        .error(function(obj, status) {
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
                    .success(function() {
                        Wait('stop');
                        $('#prompt-modal').modal('hide');
                    })
                    .error(function(obj, status) {
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
                body: `<div class='Prompt-bodyQuery'>
                        Are you sure you want to cancel the workflow below?
                    </div>
                    <div class='Prompt-bodyTarget'>
                        #${workflow.id} ${$filter('sanitize')(workflow.name)}
                    </div>`,
                action: function() {
                    Wait('start');
                    Rest.setUrl(workflow.url + 'cancel');
                    Rest.get()
                        .success(function(data) {
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
            InitiatePlaybookRun({ scope: scope, id: scope.workflow.id,
                relaunch: true, job_type: 'workflow_job' });
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
