/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['Prompt', '$filter', 'Wait', 'Rest', '$state', 'ProcessErrors', function (Prompt, $filter, Wait, Rest, $state, ProcessErrors) {
    return {
        deleteJob: function(job) {
            Prompt({
                hdr: 'Delete Job',
                body: `<div class='Prompt-bodyQuery'>
                        Are you sure you want to delete the job below?
                    </div>
                    <div class='Prompt-bodyTarget'>
                        #${job.id} ${$filter('sanitize')(job.name)}
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
        cancelJob: function(job) {
            var doCancel = function() {
                Rest.setUrl(job.url + 'cancel');
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
                            msg: `Could not cancel job.
                                Returned status: ${status}`
                        });
                    });
            };

            Prompt({
                hdr: 'Cancel Job',
                body: `<div class='Prompt-bodyQuery'>
                        Are you sure you want to cancel the job below?
                    </div>
                    <div class='Prompt-bodyTarget'>
                        #${job.id} ${$filter('sanitize')(job.name)}
                    </div>`,
                action: function() {
                    Wait('start');
                    Rest.setUrl(job.url + 'cancel');
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
                                msg: `Could not cancel job.
                                    Returned status: ${status}`
                            });
                        });
                },
                actionText: 'CANCEL'
            });
        }
    };
}];
