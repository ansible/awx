/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Groups.js
 *  Form definition for Group model
 *
 *  
 */
angular.module('GroupFormDefinition', [])
    .value(
    'GroupForm', {
        
        addTitle: 'Create Group',                            //Legend in add mode
        editTitle: '{{ name }}',                             //Legend in edit mode
        showTitle: true,
        cancelButton: false,
        name: 'group',                                       //Form name attribute
        well: true,                                          //Wrap the form with TB well
        formLabelSize: 'col-lg-3',
        formFieldSize: 'col-lg-9',
        
        titleActions: {
            copy_action: {
                'class': 'btn-success btn-xs',
                ngClick: "addGroup()",
                ngHide: "groupAddHide",
                awToolTip: "\{\{ addGroupHelp \}\}",
                dataPlacement: 'top',
                ngDisabled: "grpBtnDisable",
                icon: "icon-check",
                label: 'Copy'
                },
            create_action: {
                'class': 'btn-success btn-xs',
                ngClick: "createGroup()",
                ngHide: "groupCreateHide",
                awToolTip: "\{\{ createGroupHelp \}\}",
                dataPlacement: "top",
                ngDisabled: "grpBtnDisable",
                icon: "icon-plus",
                label: "Create New"
                },
            update_action: {
                'class': 'btn-success btn-xs',
                ngClick: "updateGroup()",
                ngHide: "groupUpdateHide",
                awToolTip: "\{\{ updateGroupHelp \}\}",
                dataPlacement: "top",
                ngDisabled: "grpBtnDisable",
                icon: "icon-cloud-download",
                label: 'Update'
                },
            delete_action: {
                'class': "btn-danger btn-xs",
                ngClick: "deleteGroup()",
                ngHide: "groupDeleteHide",
                awToolTip: "\{\{ deleteGroupHelp \}\}",
                dataPlacement: "top",
                ngDisabled: "grpBtnDisable",
                icon: "icon-trash",
                label: "Delete"
                }
            },

        fields: {
            name: {
                label: 'Name',
                type: 'text',
                addRequired: true,
                editRequired: true
                },
            description: { 
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            variables: {
                label: 'Variables',
                type: 'textarea',
                addRequired: false,
                editRequird: false, 
                rows: 10,
                'default': '---',
                dataTitle: 'Group Variables',
                dataPlacement: 'left',
                awPopOver: "<p>Variables defined here apply to all child groups and hosts.</p>" +
                    "<p>Enter variables using either JSON or YAML syntax. Use the " +
                    "radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://www.ansibleworks.com/docs/YAMLSyntax.html" target="_blank">ansibleworks.com</a></p>',
                dataContainer: 'body'
                },
            source: {
                label: 'Source',
                excludeModal: true,
                type: 'select',
                ngOptions: 'source.label for source in source_type_options',
                ngChange: 'sourceChange()',
                addRequired: false, 
                editRequired: false,
                'default': { label: 'Manual', value: '' }
                },
            source_path: {
                label: 'Script Path',
                excludeModal: true,
                ngShow: "source.value == 'file'",
                type: 'text',
                awRequiredWhen: {variable: "sourcePathRequired", init: "false" }
                },
            credential: {
                label: 'Cloud Credential',
                type: 'lookup',
                ngShow: "source.value !== ''",
                sourceModel: 'credential',
                sourceField: 'name',
                ngClick: 'lookUpCredential()',
                addRequired: false, 
                editRequired: false
                },
            source_regions: {
                label: 'Regions',
                excludeModal: true,
                type: 'text',
                ngShow: "source.value == 'rax' || source.value == 'ec2'",
                addRequired: false,
                editRequired: false,
                awMultiselect: 'source_region_choices',
                dataTitle: 'Source Regions',
                dataPlacement: 'left',
                awPopOver: "<p>Click on the regions field to see a list of regions for your cloud provider. You can select multiple regions, " +
                    "or choose <em>All</em> to include all regions. AWX will only be updated with Hosts associated with the selected regions." +
                    "</p>",
                dataContainer: 'body'
                },
            source_vars: {
                label: 'Source Variables',
                ngShow: "source.value == 'file' || source.value == 'ec2'",
                type: 'textarea',
                addRequired: false,
                editRequird: false, 
                excludeModal: true,
                rows: 10,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: 'Source Variables',
                dataPlacement: 'left',
                awPopOver: "<p>Override variables found in ec2.ini and used by the inventory update script. For a detailed description of these variables " +
                    "<a href=\"https://github.com/ansible/ansible/blob/devel/plugins/inventory/ec2.ini\" target=\"_blank\">" +
                    "view ec2.ini in the Ansible github repo.</a></p>" +
                    "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://www.ansibleworks.com/docs/YAMLSyntax.html" target="_blank">ansibleworks.com</a></p>',
                dataContainer: 'body'
                },
            /*update_interval: {
                label: 'Update Interval',
                type: 'select',
                ngOptions: 'interval.label for interval in update_interval_options',
                ngShow: "source.value !== '' && source.value !== null",
                editRequired: false,
                addRequired: false,
                'default': { label: 'none', value: 0 },
                dataTitle: 'Update Interval',
                dataPlacement: 'left',
                awPopOver: "<p>Instruct the AWX server to automatically run the inventory update process the selected number of minutes from " +
                    "the last run.</p><p>With a value set, task manager will periodically compare the amount of elapsed time from the last run. If enough time " +
                    "has elapsed, it will go ahead and start an inventory update process.</p>",
                dataContainer: 'body'
                },*/
            checkbox_group: {
                label: 'Update Options',
                type: 'checkbox_group',
                ngShow: "source.value !== '' && source.value !== null",

                fields: [
                    {
                        name: 'overwrite',
                        label: 'Overwrite',
                        type: 'checkbox',
                        ngShow: "source.value !== '' && source.value !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p>When checked all child groups and hosts not found on the remote source will be deleted from ' +
                           'the local inventory.</p><p>Unchecked any local child hosts and groups not found on the external source will ' + 
                           'remain untouched by the inventory update process.</p>',
                        dataTitle: 'Overwrite',
                        dataContainer: 'body',
                        dataPlacement: 'left',
                        labelClass: 'checkbox-options'
                        },
                    {
                        name: 'overwrite_vars',
                        label: 'Overwrite Variables',
                        type: 'checkbox',
                        ngShow: "source.value !== '' && source.value !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p>If checked, all variables for child groups and hosts will be removed and replaced by those ' + 
                          'found on the external source.</p><p>When not checked a merge will be performed, combinging local variables with ' +
                          'those found on the external source.</p>',
                        dataTitle: 'Overwrite Variables',
                        dataContainer: 'body',
                        dataPlacement: 'left',
                        labelClass: 'checkbox-options'
                        },
                    {
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
                        dataPlacement: 'left',
                        labelClass: 'checkbox-options'
                        }
                    ]
                } 
            },

        buttons: { //for now always generates <button> tags 
            
            labelClass: 'col-lg-3',
            controlClass: 'col-lg-5',

            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                "class": 'btn btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                'class': "btn btn-default",
                icon: 'icon-trash',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)
               
            }

    }); //UserForm

