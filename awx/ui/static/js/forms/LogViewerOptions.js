/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LogViewerOptions.js
 *
 *  Form definition for LogViewer.js helper
 *
 */
angular.module('LogViewerOptionsDefinition', [])
    .value('LogViewerOptionsForm', {

        name: 'status',
        well: false,
        
        fields: {
            "job_type": {
                label: "Job Type",
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
                label: "Overwrite Vars",
                type: "text",
                readonly: true
            },
            "inventory_source": {
                label: "Inv Source",
                type: "text",
                readonly: true
            }
        }
    });