/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Admins.js 
 *  List view object for Admins data model.
 *
 *
 */
angular.module('AdminListDefinition', [])
    .value(
    'AdminList', {
        
        name: 'admins',
        iterator: 'admin',
        selectTitle: 'Add Administrators',
        editTitle: 'Admins',
        selectInstructions: 'Click the Select checkbox next to each user to be added. Click the Finished button when done.', 
        
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
