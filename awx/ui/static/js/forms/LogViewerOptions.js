/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LogViewerOptions.js
 *
 *  Form definition for LogViewer.js helper
 *
 */
 /**
 * @ngdoc function
 * @name forms.function:LogViewerOptions
 * @description This form is for the page to view logs
*/
angular.module('LogViewerOptionsDefinition', [])
    .value('LogViewerOptionsForm', {

        name: 'status',
        well: false,

        fields: {
            "job_template": {
                label: "Job Template",
                type: "text",
                readonly: true
            },
            "inventory": {
                label: "Inventory",
                type: "text",
                readonly: true
            },
            "project": {
                label: "Project",
                type: "text",
                readonly: true
            },
            "playbook": {
                label: "Playbook",
                type: "text",
                readonly: true
            },
            "credential": {
                label: "Credential",
                type: "text",
                readonly: true
            },
            "cloud credential": {
                label: "Cloud Cred.",
                type: "text",
                readonly: true
            },
            "forks": {
                label: "Forks",
                type: "text",
                readonly: true
            },
            "limit": {
                label: "Limit",
                type: "text",
                readonly: true
            },
            "verbosity": {
                label: "Verbosity",
                type: "text",
                readonly: true
            },
            "job_tags": {
                label: "Job Tags",
                type: "text",
                readonly: true
            },
            "inventory_source": {
                label: "Group",
                type: "text",
                readonly: true
            },
            "source": {
                label: "Source",
                type: "text",
                readonly: true
            },
            "source_path": {
                label: "Source Path",
                type: "text",
                readonly: true
            },
            "source_regions":{
                label: "Regions",
                type: "text",
                readonly: true
            },
            "overwrite": {
                label: "Overwrite",
                type: "text",
                readonly: true
            },
            "overwrite_vars": {
                label: "Overwrite Vars",
                type: "text",
                readonly: true
            }
        }
    });