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
        emptyListText: i18n._('No Users to add'),
        disableRow: "{{ objectType === 'organization' && user.summary_fields.user_capabilities.edit === false }}",
        disableRowValue: "objectType === 'organization' && user.summary_fields.user_capabilities.edit === false",
        disableTooltip: {
            placement: 'top',
            tipWatch: 'user.tooltip'
        },
        fields: {
            first_name: {
                label: i18n._('First Name'),
                columnClass: 'd-none d-sm-flex col-md-3 col-sm-3'
            },
            last_name: {
                label: i18n._('Last Name'),
                columnClass: 'd-none d-sm-flex col-md-3 col-sm-3'
            },
            username: {
                key: true,
                label: i18n._('Username'),
                columnClass: 'col-md-5 col-sm-5 col-xs-11'
            },
        },

    };
}];
