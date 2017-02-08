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
        .factory('LogViewerStatusForm', ['i18n', function(i18n) {
        return {

            name: 'status',
            well: false,

            fields: {
                "name": {
                    label: i18n._("Name"),
                    type: "text",
                    readonly: true,
                },
                "status": {
                    label: i18n._("Status"),
                    type: "text",
                    readonly: true
                },
                "license_error": {
                    label: i18n._("License Error"),
                    type: "text",
                    readonly: true
                },
                "started": {
                    label: i18n._("Started"),
                    type: "date",
                    "filter": "longDate",
                    readonly: true
                },
                "finished": {
                    label: i18n._("Finished"),
                    type: "date",
                    "filter": "longDate",
                    readonly: true
                },
                "elapsed": {
                    label: i18n._("Elapsed"),
                    type: "text",
                    readonly: true
                },
                "launch_type": {
                    label: i18n._("Launch Type"),
                    type: "text",
                    readonly: true
                }
            }

        };}]);
