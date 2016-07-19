/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default function() {
    return {
        searchSize: 'col-lg-12 col-md-12 col-sm-12 col-xs-12',
        name: 'users',
        iterator: 'user',
        title: false,
        listTitleBadge: false,
        multiSelect: true,
        multiSelectExtended: true,
        index: false,
        hover: true,
        emptyListText : 'No Users exist',

        fields: {
            first_name: {
                label: 'First Name',
                columnClass: 'col-md-3 col-sm-3 hidden-xs'
            },
            last_name: {
                label: 'Last Name',
                columnClass: 'col-md-3 col-sm-3 hidden-xs'
            },
            username: {
                key: true,
                label: 'Username',
                columnClass: 'col-md-3 col-sm-3 col-xs-9'
            },
        },

    };
}
