/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['$q', 'Prompt', '$filter', 'Wait', 'Rest', '$state', 'ProcessErrors', 'InitiatePlaybookRun', function ($q, Prompt, $filter, Wait, Rest, $state, ProcessErrors, InitiatePlaybookRun) {
    var val = {
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
                    Rest.setUrl(job.url);
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
                    Rest.destroy()
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
                },
                actionText: 'CANCEL'
            });
        },
        relaunchJob: function(scope) {
            InitiatePlaybookRun({ scope: scope, id: scope.workflow.id,
                relaunch: true });
        }
    };
    return val;
}];
