/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  HostGroups.js
 *  Form definition for Host model
 *
 *  
 */
angular.module('HostGroupsFormDefinition', [])
    .value(
    'HostGroupsForm', {
        
        editTitle: 'Host Groups',                            //Legend in edit mode
        name: 'host',                                        //Form name attribute
        well: false,                                         //Wrap the form with TB well
        formLabelSize: 'col-lg-3',
        formFieldSize: 'col-lg-9',          

        fields: {
            groups: {
                label: 'Groups',
                type: 'select',
                multiple: true,
                ngOptions: 'group.name for group in inventory_groups',
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

    }); //UserForm

