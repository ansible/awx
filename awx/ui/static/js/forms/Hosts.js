/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
        "class": 'horizontal-narrow',
        well: false,                                         //Wrap the form with TB well          

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
                dataContainer: '#form-modal'
                },
            description: { 
                label: 'Description',
                type: 'text',
                addRequired: false,
                editRequired: false
                },
            inventory: {
                type: 'hidden',
                includeOnEdit: true, 
                includeOnAdd: true
                },
            variables: {
                label: 'Variables',
                type: 'textarea',
                addRequired: false,
                editRequird: false, 
                rows: 10,
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
                dataContainer: '#form-modal'
                }
            },

        buttons: { //for now always generates <button> tags 
            save: { 
                label: 'Save', 
                icon: 'icon-ok',
                "class": 'btn-success',
                ngClick: 'formSave()',    //$scope.function to call on click, optional
                ngDisabled: true          //Disable when $pristine or $invalid, optional
                },
            reset: { 
                ngClick: 'formReset()',
                label: 'Reset',
                icon: 'icon-remove',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)
               
            }

    }); //UserForm

