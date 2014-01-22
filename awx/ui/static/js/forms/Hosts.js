/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Hosts.js
 *  Form definition for Host model
 *
 *  
 */
angular.module('HostFormDefinition', [])
    .value(
    'HostForm', {
        
        addTitle: 'Create Host',                             //Legend in add mode
        editTitle: '{{ name }}',                             //Legend in edit mode
        name: 'host',                                        //Form name attribute
        well: false,                                         //Wrap the form with TB well
        formLabelSize: 'col-lg-3',
        formFieldSize: 'col-lg-9',          

        fields: {
            name: {
                label: 'Host Name',
                type: 'text',
                addRequired: true,
                editRequired: true,
                awPopOver: "<p>Provide a host name, ip address, or ip address:port. Examples include:</p>" +
                     "<blockquote>myserver.domain.com<br/>" +
                     "127.0.0.1<br />" + 
                     "10.1.0.140:25<br />" +
                     "server.example.com:25" +
                     "</blockquote>", 
                dataTitle: 'Host Name',
                dataPlacement: 'right',
                dataContainer: '#form-modal .modal-content'
                },
            description: { 
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            enabled: {
                label: 'Enabled?',
                type: 'checkbox',
                addRequired: false,
                editRequired: false,
                "default": true,
                awPopOver: "<p>Indicates if a host is available and should be included in running jobs.</p><p>For hosts that " +
                    "are part of an external inventory, this flag cannot be changed. It will be set by the inventory sync process.</p>",
                dataTitle: 'Host Enabled',
                dataPlacement: 'right',
                dataContainer: '#form-modal .modal-content',
                ngDisabled: 'has_inventory_sources == true'
                },
            variables: {
                label: 'Variables',
                type: 'textarea',
                addRequired: false,
                editRequird: false, 
                rows: 6,
                "class": "modal-input-xlarge",
                "default": "---",
                awPopOver: "<p>Enter variables using either JSON or YAML syntax. Use the radio button to toggle between the two.</p>" +
                    "JSON:<br />\n" +
                    "<blockquote>{<br />\"somevar\": \"somevalue\",<br />\"password\": \"magic\"<br /> }</blockquote>\n" +
                    "YAML:<br />\n" +
                    "<blockquote>---<br />somevar: somevalue<br />password: magic<br /></blockquote>\n" +
                    '<p>View JSON examples at <a href="http://www.json.org" target="_blank">www.json.org</a></p>' +
                    '<p>View YAML examples at <a href="http://www.ansibleworks.com/docs/YAMLSyntax.html" target="_blank">ansibleworks.com</a></p>',
                dataTitle: 'Host Variables',
                dataPlacement: 'right',
                dataContainer: '#form-modal .modal-content'
                },
            inventory: {
                type: 'hidden',
                includeOnEdit: true, 
                includeOnAdd: true
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)
               
            }

    }); 

