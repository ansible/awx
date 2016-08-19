/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default function() {
    return {
        searchSize: 'col-lg-12 col-md-12 col-sm-12 col-xs-12',
        name: 'teams',
        iterator: 'team',
        listTitleBadge: false,
        multiSelect: true,
        multiSelectExtended: true,
        index: false,
        hover: true,
        emptyListText : 'No Teams exist',
        fields: {
            name: {
                key: true,
                label: 'name'
            },
            organization: {
                label: 'organization',
                ngBind: 'team.summary_fields.organization.name',
                sourceModel: 'organization',
                sourceField: 'name',
                searchable: true
            }
        }

    };
}
