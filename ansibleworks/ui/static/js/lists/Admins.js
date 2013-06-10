/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Admins.js 
 *  List view object for Admins data model.
 *
 *  @dict
 */
angular.module('AdminListDefinition', [])
    .value(
    'AdminList', {
        
        name: 'admins',
        iterator: 'admin',
        selectTitle: 'Add Administrators',
        editTitle: 'Admins',
        selectInstructions: 'Click on a row to select it. Click the Finished button when done.', 
        base: 'users',
        index: true,
        
        fields: {
            username: {
                key: true,
                label: 'Username'
                },
           first_name: {
                label: 'First Name'
                },
           last_name: {
                label: 'Last Name'
                }
            },
        
        actions: {
            },

        fieldActions: {
            }
        });
