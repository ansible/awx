/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default function() {
    return {

        name: 'teams',
        iterator: 'team',
        listTitleBadge: false,
        multiSelect: true,
        multiSelectExtended: true,
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: 'name'
            },
        },

    };
}
