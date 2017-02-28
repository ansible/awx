/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default ['i18n', function(i18n){
    return {
        editTitle: '{{host.name}}',
        name: 'host',
        well: true,
        formLabelSize: 'col-lg-3',
        formFieldSize: 'col-lg-9',
        iterator: 'host',
        basePath: 'hosts',
        headerFields:{
            enabled: {
                //flag: 'host.enabled',
                class: 'Form-header-field',
                ngClick: 'toggleHostEnabled()',
                type: 'toggle',
                awToolTip: "<p>" +
                i18n._("Indicates if a host is available and should be included in running jobs.") +
                "</p><p>" +
                i18n._("For hosts that are part of an external inventory, this" +
                       " flag cannot be changed. It will be set by the inventory" +
                       " sync process.") +
                "</p>",
                dataTitle: i18n._('Host Enabled'),
                ngDisabled: 'host.has_inventory_sources'
            }
        },
        fields: {
            name: {
                label: i18n._('Host Name'),
                type: 'text',

                value: '{{name}}',
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
                dataContainer: 'body'
            },
            description: {
                label: i18n._('Description'),
                type: 'text',
            },
            variables: {
                label: i18n._('Variables'),
                type: 'textarea',
                rows: 6,
                class: 'modal-input-xlarge Form-textArea Form-formGroup--fullWidth',
                dataTitle: i18n._('Host Variables'),
                dataPlacement: 'right',
                dataContainer: 'body',
                default: '---',
                awPopOver: "<p>" + i18n._("Enter inventory variables using either JSON or YAML syntax. Use the radio button to toggle between the two.") + "</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />&emsp;\"somevar\": \"somevalue\",<br />&emsp;\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>' + i18n.sprintf(i18n._('View JSON examples at %s'), '<a href="http://www.json.org" target="_blank">www.json.org</a>') + '</p>' +
                    '<p>' + i18n.sprintf(i18n._('View YAML examples at %s'), '<a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a>') + '</p>',
            }
        },
        buttons: {
            cancel: {
                ngClick: 'formCancel()'
            },
            save: {
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: "host_form.$invalid"//true          //Disable when $pristine or $invalid, optional and when can_edit = false, for permission reasons
            }
        }
    };
}];
