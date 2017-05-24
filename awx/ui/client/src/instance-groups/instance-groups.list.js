export default ['i18n', function(i18n) {
    return {
        name:  'instance_groups' ,
        basePath: 'instance_groups',
        iterator: 'instance_group',
        listTitle: i18n._('INSTANCE GROUPS'),
        index: false,
        hover: false,

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-3 col-sm-9 col-xs-9',
                modalColumnClass: 'col-md-8',
            },
            capacity: {
                label: i18n._('Capacity'),
                nosort: true,
            },
            running_jobs: {
                label: i18n._('Running Jobs'),
                nosort: true,
            },
        }
    };
}];
