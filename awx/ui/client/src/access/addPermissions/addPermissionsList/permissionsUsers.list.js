/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default function() {
    return {
        name: 'users',
        iterator: 'user',
        defaultSearchParams: function(term){
            return {or__username__icontains: term,
                    or__first_name__icontains: term,
                    or__last_name__icontains: term
                };
        },
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
