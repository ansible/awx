/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/



export default function(){
    return {
        name:  'notifications' ,
        listTitle: 'Notifications',
        iterator: 'notification',
        index: false,
        hover: false,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8'
            },
            description: {
                label: 'Description',
                excludeModal: true,
                columnClass: 'col-md-4 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addNotification()',
                awToolTip: 'Create a new custom inventory',
                actionClass: 'btn List-buttonSubmit',
                buttonContent: '&#43; ADD'
            }
        },

        fieldActions: {

            columnClass: 'col-md-2 col-sm-3 col-xs-3',

            edit: {
                ngClick: "editNotification(inventory_script.id)",
                icon: 'fa-edit',
                label: 'Edit',
                "class": 'btn-sm',
                awToolTip: 'Edit credential',
                dataPlacement: 'top'
            },
            "delete": {
                ngClick: "deleteNotification(notification.id, notification.name)",
                icon: 'fa-trash',
                label: 'Delete',
                "class": 'btn-sm',
                awToolTip: 'Delete credential',
                dataPlacement: 'top'
            }
        }
    };
}
