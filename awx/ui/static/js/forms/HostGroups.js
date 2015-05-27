/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
 /**
 * @ngdoc function
 * @name forms.function:HostGroups
 * @description This form is for groups of hosts on the inventory page
*/

export default
    angular.module('HostGroupsFormDefinition', [])
        .value('HostGroupsForm', {

            editTitle: 'Host Groups',
            name: 'host',
            well: false,
            formLabelSize: 'col-lg-3',
            formFieldSize: 'col-lg-9',

            fields: {
                groups: {
                    label: 'Groups',
                    type: 'select',
                    multiple: true,
                    ngOptions: 'group.name for group in inventory_groups track by group.value',
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
                    ngClick: 'formSave()',
                    ngDisabled: true
                },
                reset: {
                    ngClick: 'formReset()',
                    ngDisabled: true
                }
            },

            related: { }

        }); //UserForm
