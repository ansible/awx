/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default ['i18n', function(i18n) {
    return {
        name: 'users',
        iterator: 'user',
        title: false,
        listTitleBadge: false,
        multiSelect: true,
        multiSelectExtended: true,
        index: false,
        hover: true,
        emptyListText : i18n._('No Users exist'),
        fields: {
            first_name: {
                label: i18n._('First Name'),
                columnClass: 'col-md-3 col-sm-3 hidden-xs'
            },
            last_name: {
                label: i18n._('Last Name'),
                columnClass: 'col-md-3 col-sm-3 hidden-xs'
            },
            username: {
                key: true,
                label: i18n._('Username'),
                columnClass: 'col-md-5 col-sm-5 col-xs-11'
            },
        },

    };
}];
