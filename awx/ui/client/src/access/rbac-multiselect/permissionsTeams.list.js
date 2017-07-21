/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default ['i18n', function(i18n) {
    return {
        name: 'teams',
        iterator: 'team',
        listTitleBadge: false,
        multiSelect: true,
        multiSelectExtended: true,
        index: false,
        hover: true,
        emptyListText : i18n._('No Teams exist'),
        fields: {
            name: {
                key: true,
                label: i18n._('name')
            },
            organization: {
                label: i18n._('organization'),
                ngBind: 'team.summary_fields.organization.name',
                sourceModel: 'organization',
                sourceField: 'name',
                searchable: true
            }
        }

    };
}];
