/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobTemplates.js
 *  List view object for Job Templates data model.
 *
 *
 */

'use strict';

angular.module('ConfigureTowerJobsListDefinition', [])
    .value('ConfigureTowerJobsList', {

        name: 'configure_jobs',
        iterator: 'configure_job',
        selectTitle: 'Configure Tower Jobs',
        editTitle: 'Configure Tower Jobs',
        index: false,
        hover: true,

        fields: {
            name: {
                // key: true,
                label: 'Name',
                columnClass: 'col-sm-4 col-xs-4'
            },
            description: {
                label: 'Description',
                columnClass: 'col-sm-6 col-xs-6 hidden-sm hidden-xs'
            }
        },
        fieldActions: {
            submit: {
                label: 'Launch',
                mode: 'all',
                ngClick: 'submitJob(configure_job.id)',
                awToolTip: 'Start a job using this template',
                dataPlacement: 'top'
            },
            schedule: {
                label: 'Schedule',
                mode: 'all',
                ngClick: 'configureSchedule(configure_job.id)', // '#/job_templates/{{ configure_job.id }}/schedules',
                awToolTip: 'Schedule future job template runs',
                dataPlacement: 'top',
            },
            delete: {
                label: 'Delete Schedule',
                mode: 'all',
                ngClick: 'deleteSystemSchedule(configure_job.id)', // '#/job_templates/{{ configure_job.id }}/schedules',
                awToolTip: 'Delete the schedule ',
                dataPlacement: 'top',
            }
        }
    });
