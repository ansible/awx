/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default function(){
    return {
        name: 'configure_jobs',
        iterator: 'configure_job',
        index: false,
        hover: true,

        fields: {
            name: {
                label: 'Name',
                columnClass: 'col-sm-4 col-xs-4'
            },
            description: {
                label: 'Description',
                columnClass: 'col-sm-6 col-xs-6 hidden-sm hidden-xs'
            }
        },
        actions: {
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                icon: "icon-comments-alt",
                mode: 'edit',
                awFeature: 'activity_streams'
            }
        },
        fieldActions: {
            submit: {
                label: 'Launch',
                mode: 'all',
                ngClick: 'submitJob(configure_job.id, configure_job.name)',
                awToolTip: 'Start a job using this template',
                dataPlacement: 'top'
            },
            schedule: {
                label: 'Schedule',
                mode: 'all',
                ngClick: 'configureSchedule()',
                awToolTip: 'Schedule future job template runs',
                dataPlacement: 'top',
            }
        }
    };
}
