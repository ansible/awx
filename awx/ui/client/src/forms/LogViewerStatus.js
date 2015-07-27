/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:LogViewerStatus
 * @description Form definition for LogViewer.js helper
*/

export default
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
                    "filter": "longDate",
                    readonly: true
                },
                "finished": {
                    label: "Finished",
                    type: "date",
                    "filter": "longDate",
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
