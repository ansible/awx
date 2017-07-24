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
        listTitle: 'MANAGEMENT JOBS',

        fields: {
            name: {
                label: 'Name',
                columnClass: 'col-sm-4 col-xs-4',
                awToolTip: '{{configure_job.description | sanitize}}',
                dataPlacement: 'top'
            }
        },
        actions: {

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
