/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Groups
 * @description This form is for adding/editing a Group on the inventory page
*/

export default
    angular.module('GroupFormDefinition', [])
        .value('GroupFormObject', {

            addTitle: 'Create Group',
            editTitle: '{{ name }}',
            showTitle: true,
            name: 'group',
            well: false,

            fields: {
                name: {
                    label: 'Name',
                    type: 'text',
                    addRequired: true,
                    editRequired: true,
                    tab: 'properties'
                },
                description: {
                    label: 'Description',
                    type: 'text',
                    addRequired: false,
                    editRequired: false,
                    tab: 'properties'
                },
                variables: {
                    label: 'Variables',
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    addRequired: false,
                    editRequird: false,
                    rows: 12,
                    'default': '---',
                    dataTitle: 'Group Variables',
                    dataPlacement: 'right',
                    awPopOver: "<p>Variables defined here apply to all child groups and hosts.</p>" +
                        "<p>Enter variables using either JSON or YAML syntax. Use the " +
                        "radio button to toggle between the two.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp; \"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                        '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                        '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                    dataContainer: 'body',
                    tab: 'properties'
                },
                source: {
                    label: 'Source',
                    type: 'select',
                    ngOptions: 'source.label for source in source_type_options track by source.value',
                    ngChange: 'sourceChange(source)',
                    addRequired: false,
                    editRequired: false,
                    ngModel: 'source'
                },
                credential: {
                    label: 'Cloud Credential',
                    type: 'lookup',
                    ngShow: "source && source.value !== 'manual' && source.value !== 'custom'",
                    sourceModel: 'credential',
                    sourceField: 'name',
                    ngClick: 'lookUpCredential()',
                    awRequiredWhen: {
                        reqExpression: "cloudCredentialRequired",
                        init: "false"
                    }
                },
                source_regions: {
                    label: 'Regions',
                    type: 'select',
                    ngOptions: 'source.label for source in source_region_choices track by source.value',
                    multiSelect: true,
                    ngShow: "source && (source.value == 'rax' || source.value == 'ec2' || source.value == 'gce' || source.value == 'azure' || source.value == 'azure_rm')",
                    addRequired: false,
                    editRequired: false,
                    dataTitle: 'Source Regions',
                    dataPlacement: 'right',
                    awPopOver: "<p>Click on the regions field to see a list of regions for your cloud provider. You can select multiple regions, " +
                        "or choose <em>All</em> to include all regions. Tower will only be updated with Hosts associated with the selected regions." +
                        "</p>",
                    dataContainer: 'body'
                },
                instance_filters: {
                    label: 'Instance Filters',
                    type: 'text',
                    ngShow: "source && source.value == 'ec2'",
                    addRequired: false,
                    editRequired: false,
                    dataTitle: 'Instance Filters',
                    dataPlacement: 'right',
                    awPopOver: "<p>Provide a comma-separated list of filter expressions. " +
                        "Hosts are imported to Tower when <em>ANY</em> of the filters match.</p>" +
                        "Limit to hosts having a tag:<br />\n" +
                        "<blockquote>tag-key=TowerManaged</blockquote>\n" +
                        "Limit to hosts using either key pair:<br />\n" +
                        "<blockquote>key-name=staging, key-name=production</blockquote>\n" +
                        "Limit to hosts where the Name tag begins with <em>test</em>:<br />\n" +
                        "<blockquote>tag:Name=test*</blockquote>\n" +
                        "<p>View the <a href=\"http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-DescribeInstances.html\" target=\"_blank\">Describe Instances documentation</a> " +
                        "for a complete list of supported filters.</p>",
                    dataContainer: 'body'
                },
                group_by: {
                    label: 'Only Group By',
                    type: 'select',
                    ngShow: "source && source.value == 'ec2'",
                    ngOptions: 'source.label for source in group_by_choices track by source.value',
                    addRequired: false,
                    editRequired: false,
                    multiSelect: true,
                    dataTitle: 'Only Group By',
                    dataPlacement: 'right',
                    awPopOver: "<p>Select which groups to create automatically. " +
                        "Tower will create group names similar to the following examples based on the options selected:</p><ul>" +
                        "<li>Availability Zone: <strong>zones &raquo; us-east-1b</strong></li>" +
                        "<li>Image ID: <strong>images &raquo; ami-b007ab1e</strong></li>" +
                        "<li>Instance ID: <strong>instances &raquo; i-ca11ab1e</strong></li>" +
                        "<li>Instance Type: <strong>types &raquo; type_m1_medium</strong></li>" +
                        "<li>Key Name: <strong>keys &raquo; key_testing</strong></li>" +
                        "<li>Region: <strong>regions &raquo; us-east-1</strong></li>" +
                        "<li>Security Group: <strong>security_groups &raquo; security_group_default</strong></li>" +
                        "<li>Tags: <strong>tags &raquo; tag_Name &raquo; tag_Name_host1</strong></li>" +
                        "<li>VPC ID: <strong>vpcs &raquo; vpc-5ca1ab1e</strong></li>" +
                        "</ul><p>If blank, all groups above are created except <em>Instance ID</em>.</p>",
                    dataContainer: 'body'
                },
                inventory_script: {
                    label :  "Custom Inventory Script",
                    type: 'lookup',
                    ngShow: "source && source.value === 'custom'",
                    sourceModel: 'inventory_script',
                    sourceField: 'name',
                    ngClick: 'lookUpInventory_script()' ,
                    addRequired: true,
                    editRequired: true,
                    ngRequired: "source && source.value === 'custom'",
                },
                custom_variables: {
                    id: 'custom_variables',
                    label: 'Environment Variables', //"{{vars_label}}" ,
                    ngShow: "source && source.value=='custom' ",
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    addRequired: false,
                    editRequired: false,
                    rows: 6,
                    'default': '---',
                    parseTypeName: 'envParseType',
                    dataTitle: "Environment Variables",
                    dataPlacement: 'right',
                    awPopOver:  "<p>Provide key/value pairs using either YAML or JSON.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n",
                    dataContainer: 'body'
                },
                ec2_variables: {
                    id: 'ec2_variables',
                    label: 'Source Variables', //"{{vars_label}}" ,
                    ngShow: "source && source.value == 'ec2'",
                    type: 'textarea',
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    addRequired: false,
                    editRequird: false,
                    rows: 6,
                    'default': '---',
                    parseTypeName: 'envParseType',
                    dataTitle: "Source Variables",
                    dataPlacement: 'right',
                    awPopOver: "<p>Override variables found in ec2.ini and used by the inventory update script. For a detailed description of these variables " +
                        "<a href=\"https://github.com/ansible/ansible/blob/devel/contrib/inventory/ec2.ini\" target=\"_blank\">" +
                        "view ec2.ini in the Ansible github repo.</a></p>" +
                        "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                        '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                        '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                    dataContainer: 'body'
                },
                vmware_variables: {
                    id: 'vmware_variables',
                    label: 'Source Variables', //"{{vars_label}}" ,

                    ngShow: "source && source.value == 'vmware'",
                    type: 'textarea',
                    addRequired: false,
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    editRequird: false,
                    rows: 6,
                    'default': '---',
                    parseTypeName: 'envParseType',
                    dataTitle: "Source Variables",
                    dataPlacement: 'right',
                    awPopOver: "<p>Override variables found in vmware.ini and used by the inventory update script. For a detailed description of these variables " +
                        "<a href=\"https://github.com/ansible/ansible/blob/devel/contrib/inventory/vmware.ini\" target=\"_blank\">" +
                        "view vmware.ini in the Ansible github repo.</a></p>" +
                        "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                        '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                        '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                    dataContainer: 'body'
                },
                openstack_variables: {
                    id: 'openstack_variables',
                    label: 'Source Variables', //"{{vars_label}}" ,

                    ngShow: "source && source.value == 'openstack'",
                    type: 'textarea',
                    addRequired: false,
                    class: 'Form-textAreaLabel Form-formGroup--fullWidth',
                    editRequird: false,
                    rows: 6,
                    'default': '---',
                    parseTypeName: 'envParseType',
                    dataTitle: "Source Variables",
                    dataPlacement: 'right',
                    awPopOver: "<p>Override variables found in openstack.yml and used by the inventory update script. For an example variable configuration " +
                        "<a href=\"https://github.com/ansible/ansible/blob/devel/contrib/inventory/openstack.yml\" target=\"_blank\">" +
                        "view openstack.yml in the Ansible github repo.</a></p>" +
                        "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                        '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                        '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                    dataContainer: 'body'
                },
                checkbox_group: {
                    label: 'Update Options',
                    type: 'checkbox_group',
                    ngShow: "source && (source.value !== 'manual' && source.value !== null)",

                    fields: [{
                        name: 'overwrite',
                        label: 'Overwrite',
                        type: 'checkbox',
                        ngShow: "source.value !== 'manual' && source.value !== null",
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
                        ngShow: "source.value !== 'manual' && source.value !== null",
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
                        ngShow: "source.value !== 'manual' && source.value !== null",
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
                    ngShow: "source && source.value !== 'manual' && update_on_launch",
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
                save: {
                    ngClick: 'formSave()'
                },
                cancel: {
                    ngClick: 'formCancel()'
                }
            },

            related: {
                "notifications": {
                    include: "NotificationsList"
                }
            },
            relatedSets: function() {
                return {
                    notifications: {
                        iterator: 'notification',
                        url: 'api/v1/notification_templates/'
                    }
                };
            }

        })
        .factory('GroupForm', ['GroupFormObject', 'NotificationsList',
        function(GroupFormObject, NotificationsList) {
            return function() {
                var itm;

                for (itm in GroupFormObject.related) {
                    if (GroupFormObject.related[itm].include === "NotificationsList") {
                        GroupFormObject.related[itm] = NotificationsList;
                        GroupFormObject.related[itm].generateList = true;
                        GroupFormObject.related[itm].disabled = "source === undefined";
                    }
                }
                return GroupFormObject;
            };
        }]);
