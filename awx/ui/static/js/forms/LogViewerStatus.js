/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LogViewerStatus.js
 *
 *  Form definition for LogViewer.js helper
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:LogViewerStatus
 * @description Form definition for LogViewer.js helper
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
                type: "date",
                "filter": "date:'MM/dd/yy HH:mm:ss'",
                readonly: true
            },
            "finished": {
                label: "Finished",
                type: "date",
                "filter": "date:'MM/dd/yy HH:mm:ss'",
                readonly: true
            },
            "elapsed": {
                label: "Elapsed",
                type: "text",
                readonly: true
            },
            "launch_type": {
                label: "Launch Type",
                type: "text",
                readonly: true
            }
        }

    });