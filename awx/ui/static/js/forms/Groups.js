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
        editTitle: 'Group Properties: {{ name }}',           //Legend in edit mode
        showTitle: true,
        cancelButton: false,
        name: 'group',                                       //Form name attribute
        well: false,                                         //Wrap the form with TB well
        formLabelSize: 'col-lg-3',
        formFieldSize: 'col-lg-9',
        
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
                awPopOver: "<p>Variables defined here apply to all child groups and hosts. Enter variables using either JSON or YAML syntax. Use the " +
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
                'default': { label: 'Manual', value: null }
                },
            source_path: {
                label: 'Script Path',
                excludeModal: true,
                ngShow: "source.value == 'file'",
                type: 'text',
                awRequiredWhen: {variable: "sourcePathRequired", init: "false" }
                },
            source_env: {
                label: 'Script Environment Variables',
                ngShow: "source.value == 'file'",
                type: 'textarea',
                addRequired: false,
                editRequird: false, 
                excludeModal: true,
                rows: 10,
                'default': '---',
                parseTypeName: 'envParseType',
                dataTitle: 'Script Environment Variables',
                dataPlacement: 'left',
                awPopOver: "<p>Define environment variables here that will be referenced by the inventory script at runtime. " +
                    "Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://www.ansibleworks.com/docs/YAMLSyntax.html" target="_blank">ansibleworks.com</a></p>',
                dataContainer: 'body',
                awPopOverRight: true
                },
            source_username: {
                labelBind: 'sourceUsernameLabel',
                excludeModal: true,
                type: 'text',
                ngShow: "source.value == 'rackspace' || source.value == 'ec2'",
                awRequiredWhen: {variable: "sourceUsernameRequired", init: "false" }
                },
            source_password: {
                labelBind: 'sourcePasswordLabel',
                excludeModal: true,
                type: 'password',
                ngShow: "source.value == 'rackspace' || source.value == 'ec2'",
                editRequired: false,
                addRequired: false,
                ngChange: "clearPWConfirm('source_password_confirm')",
                ask: true,
                clear: true,
                associated: 'source_password_confirm',
                autocomplete: false
                },
            source_password_confirm: {
                labelBind: 'sourcePasswordConfirmLabel',
                type: 'password',
                ngShow: "source.value == 'rackspace' || source.value == 'ec2'",
                addRequired: false,
                editRequired: false,
                awPassMatch: true,
                associated: 'source_password',
                autocomplete: false
                },
            source_regions: {
                label: 'Regions',
                excludeModal: true,
                type: 'text',
                ngShow: "source.value == 'rackspace' || source.value == 'ec2'",
                addRequired: false,
                editRequired: false
                },
            source_tags: {
                label: 'Tags',
                excludeModal: true,
                type: 'text',
                ngShow: "source.value == 'rackspace' || source.value == 'ec2'",
                addRequired: false,
                editRequired: false
                },
            checkbox_group: {
                label: 'Update Options',
                type: 'checkbox_group',
                ngShow: "source.value !== '' && source.value !== null",

                fields: [
                    {
                        name: 'overwite_hosts',
                        label: 'Overwrite Hosts',
                        type: 'checkbox',
                        ngShow: "source.value !== '' && source.value !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p>Replace AWX inventory hosts with cloud inventory hosts.</p>',
                        dataTitle: 'Overwrite Hosts',
                        dataContainer: 'body',
                        dataPlacement: 'left',
                        labelClass: 'checkbox-options',
                        inline: false
                        },
                    {
                        name: 'overwite_vars',
                        label: 'Overwrite Variables',
                        type: 'checkbox',
                        ngShow: "source.value !== '' && source.value !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p></p>',
                        dataTitle: 'Overwrite Variables',
                        dataContainer: 'body',
                        dataPlacement: 'left',
                        labelClass: 'checkbox-options',
                        inline: false
                        },
                    {
                        name: 'keep_vars',
                        label: 'Keep Variables',
                        type: 'checkbox',
                        ngShow: "source.value !== '' && source.value !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p></p>',
                        dataTitle: 'Keep Variables',
                        dataContainer: 'body',
                        dataPlacement: 'left',
                        labelClass: 'checkbox-options',
                        inline: false
                        },
                    {
                        name: 'update_on_launch',
                        label: 'Update on Launch',
                        type: 'checkbox',
                        ngShow: "source.value !== '' && source.value !== null",
                        addRequired: false,
                        editRequired: false,
                        awPopOver: '<p>Each time a job runs using this inventory, refresh the inventory from the selected source</p>',
                        dataTitle: 'Update on Launch',
                        dataContainer: 'body',
                        dataPlacement: 'left',
                        labelClass: 'checkbox-options',
                        inline: false
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

