/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

export default function(){
    return {
        editTitle: '{{host.name}}',
        name: 'host',
        well: true,
        formLabelSize: 'col-lg-3',
        formFieldSize: 'col-lg-9',
        headerFields:{
            enabled: {
                label: 'Enabled?',
                type: 'checkbox',
                editRequired: false,
                'default': true,
            awPopOver: "<p>Indicates if a host is available and should be included in running jobs.</p><p>For hosts that " +
                "are part of an external inventory, this flag cannot be changed. It will be set by the inventory sync process.</p>",
            dataTitle: 'Host Enabled'
            }
        },
        fields: {
            enabled: {
                label: 'Status',
                columnClass: 'List-staticColumn--toggle',
                type: 'toggle',
                ngClick: 'toggleHostEnabled(host)',
                searchable: false,
                nosort: true
            },
            name: {
                label: 'Host Name',
                type: 'text',
                editRequired: true,
            awPopOver: "<p>Provide a host name, ip address, or ip address:port. Examples include:</p>" +
                "<blockquote>myserver.domain.com<br/>" +
                "127.0.0.1<br />" +
                "10.1.0.140:25<br />" +
                "server.example.com:25" +
                "</blockquote>",
            },
            description: {
                label: 'Description',
                type: 'text',
                editRequired: false
            },
            variables: {
                label: 'Variables',
                type: 'textarea',
                editRequired: false,
                rows: 6,
                default: '---',
                 awPopOver: "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://docs.ansible.com/YAMLSyntax.html" target="_blank">docs.ansible.com</a></p>',                  
            }
        }
    }
};