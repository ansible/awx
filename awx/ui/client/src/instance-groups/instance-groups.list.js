export default ['i18n', function(i18n) {
    return {
        name:  'instance_groups' ,
        basePath: 'instance_groups',
        iterator: 'instance_group',
        editTitle: i18n._('INSTANCE GROUPS'),
        listTitle: i18n._('INSTANCE GROUPS'),
        emptyListText: i18n._('THERE ARE CURRENTLY NO INSTANCE GROUPS DEFINED'),
        index: false,
        hover: false,

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8',
                uiSref: 'instanceGroups.instances.list({instance_group_id: instance_group.id})',
                ngClass: "{'isActive' : isActive()}"
            },
            consumed_capacity: {
                label: i18n._('Capacity'),
                nosort: true,
            },
            jobs_running: {
                label: i18n._('Running Jobs'),
                nosort: true,
            },
        }
    };
}];
