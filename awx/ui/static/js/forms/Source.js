/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Groups.js
 *  Form definition for Group model
 *
 *
 */
  /**
 * @ngdoc function
 * @name forms.function:Source
 * @description This form is for group model
*/
angular.module('SourceFormDefinition', [])
    .value('SourceForm', {

        addTitle: 'Create Source',
        editTitle: 'Edit Source',
        showTitle: false,
        cancelButton: false,
        name: 'source',
        well: false,

        fields: {
            source: {
                label: 'Source',
                type: 'select',
                ngOptions: 'source.label for source in source_type_options track by source.value',
                ngChange: 'sourceChange()',
                addRequired: false,
                editRequired: false
            },
            source_path: {
                label: 'Script Path',
                ngShow: "source && source.value == 'file'",
                type: 'text',
                awRequiredWhen: {
                    variable: "sourcePathRequired",
                    init: "false"
                }
            },
            credential: {
                label: 'Cloud Credential',
                type: 'lookup',
                ngShow: "source && source.value !== ''",
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookUpCredential()',
                addRequired: false,
                editRequired: false
            },
            source_regions: {
                label: 'Regions',
                type: 'text',
                ngShow: "source && (source.value == 'rax' || source.value == 'ec2' || source.value == 'gce' || source.value == 'azure')",
                addRequired: false,
                editRequired: false,
                awMultiselect: 'source_region_choices',
                dataTitle: 'Source Regions',
                dataPlacement: 'right',
                awPopOver: "<p>Click on the regions field to see a list of regions for your cloud provider. You can select multiple regions, " +
                    "or choose <em>All</em> to include all regions. Tower will only be updated with Hosts associated with the selected regions." +
                    "</p>",
                dataContainer: 'body'
            },
            source_vars: {
                label: 'Source Variables',
                ngShow: "source && (source.value == 'file' || source.value == 'ec2')",
                type: 'textarea',
                addRequired: false,
                editRequird: false,
                rows: 6,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: 'Source Variables',
                dataPlacement: 'right',
                awPopOver: "<p>Override variables found in ec2.ini and used by the inventory update script. For a detailed description of these variables " +
                    "<a href=\"https://github.com/ansible/ansible/blob/devel/plugins/inventory/ec2.ini\" target=\"_blank\">" +
                    "view ec2.ini in the Ansible github repo.</a></p>" +
                    "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body'
            },
            checkbox_group: {
                label: 'Update Options',
                type: 'checkbox_group',
                ngShow: "source && (source.value !== '' && source.value !== null)",

                fields: [{
                    name: 'overwrite',
                    label: 'Overwrite',
                    type: 'checkbox',
                    ngShow: "source.value !== '' && source.value !== null",
                    addRequired: false,
                    editRequired: false,
                    awPopOver: '<p>If checked, all child groups and hosts not found on the external source will be deleted from ' +
                        'the local inventory.</p><p>When not checked, local child hosts and groups not found on the external source will ' +
                        'remain untouched by the inventory update process.</p>',
                    dataTitle: 'Overwrite',
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options'
                }, {
                    name: 'overwrite_vars',
                    label: 'Overwrite Variables',
                    type: 'checkbox',
                    ngShow: "source.value !== '' && source.value !== null",
                    addRequired: false,
                    editRequired: false,
                    awPopOver: '<p>If checked, all variables for child groups and hosts will be removed and replaced by those ' +
                        'found on the external source.</p><p>When not checked, a merge will be performed, combining local variables with ' +
                        'those found on the external source.</p>',
                    dataTitle: 'Overwrite Variables',
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options'
                }, {
                    name: 'update_on_launch',
                    label: 'Update on Launch',
                    type: 'checkbox',
                    ngShow: "source.value !== '' && source.value !== null",
                    addRequired: false,
                    editRequired: false,
                    awPopOver: '<p>Each time a job runs using this inventory, refresh the inventory from the selected source before ' +
                        'executing job tasks.</p>',
                    dataTitle: 'Update on Launch',
                    dataContainer: 'body',
                    dataPlacement: 'right',
                    labelClass: 'checkbox-options'
                }]
            },
            update_cache_timeout: {
                label: "Cache Timeout <span class=\"small-text\"> (seconds)</span>",
                id: 'source-cache-timeout',
                type: 'number',
                integer: true,
                min: 0,
                ngShow: "source && source.value !== '' && update_on_launch",
                spinner: true,
                "default": 0,
                addRequired: false,
                editRequired: false,
                awPopOver: '<p>Time in seconds to consider an inventory sync to be current. During job runs and callbacks the task system will ' +
                    'evaluate the timestamp of the latest sync. If it is older than Cache Timeout, it is not considered current, ' +
                    'and a new inventory sync will be performed.</p>',
                dataTitle: 'Cache Timeout',
                dataPlacement: 'right',
                dataContainer: "body"
            }
        },

        buttons: {

        },

        related: { }

    });
