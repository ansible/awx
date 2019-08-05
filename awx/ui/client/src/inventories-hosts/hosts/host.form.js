/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name forms.function:Hosts
 * @description This form is for adding/editing a host on the inventory page
*/

export default ['i18n',
function(i18n) {
        return {

            addTitle: i18n._('CREATE HOST'),
            editTitle: '{{ host.name }}',
            name: 'host',
            basePath: 'hosts',
            well: false,
            formLabelSize: 'col-lg-3',
            formFieldSize: 'col-lg-9',
            iterator: 'host',
            detailsClick: "$state.go('hosts.edit', null, {reload:true})",
            activeEditState: 'hosts.edit',
            stateTree: 'hosts',
            headerFields:{
                enabled: {
                    class: 'Form-header-field',
                    ngClick: 'toggleHostEnabled(host)',
                    type: 'toggle',
                    awToolTip: "<p>" +
                        i18n._("Indicates if a host is available and should be included in running jobs.") +
                        "</p><p>" +
                        i18n._("For hosts that are part of an external" +
                               " inventory, this may be" +
                               " reset by the inventory sync process.") +
                        "</p>",
                    dataTitle: i18n._('Host Enabled'),
                }
            },
            fields: {
                name: {
                    label: i18n._('Host Name'),
                    type: 'text',
                    required: true,
                    awPopOver: "<p>" +
                    i18n._("Provide a host name, ip address, or ip address:port. Examples include:") +
                        "</p>" +
                        "<blockquote>myserver.domain.com<br/>" +
                        "127.0.0.1<br />" +
                        "10.1.0.140:25<br />" +
                        "server.example.com:25" +
                        "</blockquote>",
                    dataTitle: i18n._('Host Name'),
                    dataPlacement: 'right',
                    dataContainer: 'body',
                    ngDisabled: '!(host.summary_fields.user_capabilities.edit || canAdd)'
                },
                description: {
                    label: i18n._('Description'),
                    ngDisabled: '!(host.summary_fields.user_capabilities.edit || canAdd)',
                    type: 'text'
                },
                variables: {
                    label: i18n._('Variables'),
                    type: 'code_mirror',
                    variables: 'variables',
                    class: 'Form-formGroup--fullWidth',
                    "default": "---",
                    awPopOver: "<p>" + i18n._("Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                        "JSON:<br />\n" +
                        "<blockquote>{<br />&emsp;&quot;somevar&quot;: &quot;somevalue&quot;,<br />&emsp;&quot;password&quot;: &quot;magic&quot;<br /> }</blockquote>\n" +
                        "YAML:<br />\n" +
                        "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                        '<p>' + i18n.sprintf(i18n._('View JSON examples at %s'), '<a href=&quot;http://www.json.org&quot; target=&quot;_blank&quot;>www.json.org</a>') + '</p>' +
                        '<p>' + i18n.sprintf(i18n._('View YAML examples at %s'), '<a href=&quot;http://docs.ansible.com/YAMLSyntax.html&quot; target=&quot;_blank&quot;>docs.ansible.com</a>') + '</p>',
                }
            },

            buttons: {
                cancel: {
                    ngClick: 'formCancel()',
                    ngShow: '(host.summary_fields.user_capabilities.edit || canAdd)'
                },
                close: {
                    ngClick: 'formCancel()',
                    ngShow: '!(host.summary_fields.user_capabilities.edit || canAdd)'
                },
                save: {
                    ngClick: 'formSave()',
                    ngDisabled: true,
                    ngShow: '(host.summary_fields.user_capabilities.edit || canAdd)'
                }
            },

            related: {
                ansible_facts: {
                    name: 'ansible_facts',
                    awToolTip: i18n._('Please save before viewing facts.'),
                    dataPlacement: 'top',
                    title: i18n._('Facts'),
                    skipGenerator: true
                },
                groups: {
                    name: 'groups',
                    awToolTip: i18n._('Please save before defining groups.'),
                    dataPlacement: 'top',
                    ngClick: "$state.go('hosts.edit.groups')",
                    title: i18n._('Groups'),
                    iterator: 'group',
                    skipGenerator: true
                },
                insights: {
                    name: 'insights',
                    awToolTip: i18n._('Please save before viewing Insights.'),
                    dataPlacement: 'top',
                    title: i18n._('Insights'),
                    skipGenerator: true,
                    ngIf: "host.insights_system_id!==null && host.summary_fields.inventory.hasOwnProperty('insights_credential_id')"
                },
                completed_jobs: {
                    name: 'completed_jobs',
                    title: i18n._('Completed Jobs'),
                    skipGenerator: true
                }
            }
        };
    }];
