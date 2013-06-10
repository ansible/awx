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
        editTitle: '{{ name }}',                             //Legend in edit mode
        name: 'group',                                       //Form name attribute
        well: false,                                         //Wrap the form with TB well          

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
                "default": "\{\}",
                dataTitle: 'Group Variables',
                dataPlacement: 'right',
                awPopOver: '<p>Enter variables as JSON. Both the key and value must be wrapped in double quotes. ' +
                    'Separate variables with commas, and wrap the entire string with { }. ' +
                    '&nbsp;For example:</p><p>{<br\>&quot;ntp_server&quot;: &quot;ntp.example.com&quot;,<br \>' + 
                    '&quot;proxy&quot;: &quot;proxy.example.com&quot;<br \>}</p><p>See additional JSON examples at <a href="' +
                    'http://www.json.org" target="_blank">www.json.org</a></p>'
                }
            },

        buttons: { //for now always generates <button> tags 
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
                icon: 'icon-remove',
                ngDisabled: true          //Disabled when $pristine
                }
            },

        related: { //related colletions (and maybe items?)
               
            }

    }); //UserForm

