/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Groups.js
 *  Form definition for Group model
 *
 *
 */
angular.module('GroupFormDefinition', [])
    .value('GroupForm', {

        addTitle: 'Create Group',
        editTitle: 'Edit Group',
        showTitle: true,
        cancelButton: false,
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
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',
                dataContainer: 'body',
                tab: 'properties'
            }
        },

        buttons: { },

        related: { }

    });