export default ['i18n', function(i18n) {
    return {
        name:  'instances' ,
        iterator: 'instance',
        listTitle: false,
        index: false,
        hover: false,
        tabs: true,
        well: true,

        fields: {
            hostname: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8',
                uiSref: 'instanceGroups.instances.list.job({instance_id: instance.id})'
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
