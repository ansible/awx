/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LogViewerStatus.js
 *
 *  Form definition for LogViewer.js helper
 *
 */
angular.module('LogViewerStatusDefinition', [])
    .value('LogViewerStatusForm', {

        name: 'status',
        well: false,
        
        fields: {
            "name": {
                label: "Name",
                type: "text",
                readonly: true,
            },
            "created": {
                label: "Created",
                type: "text",
                readonly: true
            },
            "modified": {
                label: "Modified",
                type: "text",
                readonly: true
            },
            "unified_job_template": {
                label: "Job Template",
                type: "text",
                readonly: true
            },
            "launch_type": {
                label: "Launch Type",
                type: "text",
                readonly: true
            },
            "status": {
                label: "Status",
                type: "text",
                readonly: true
            },
            "license_error": {
                label: "License Error",
                type: "text",
                readonly: true
            },
            "started": {
                label: "Started",
                type: "text",
                readonly: true
            },
            "finished": {
                label: "Finished",
                type: "text",
                readonly: true
            },
            "elapsed": {
                label: "Elapsed",
                type: "text",
                readonly: true
            }
        }
        
    });