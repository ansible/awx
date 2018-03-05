export default ['i18n', function(i18n) {
    return {

        name: 'applications',
        search: {
            order_by: 'id'
        },
        iterator: 'application',
        // TODO: change
        basePath: 'projects',
        listTitle: i18n._('APPLICATIONS'),
        index: false,
        hover: true,

        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-md-3 col-sm-3 col-xs-9'
            },
        }
    };}];
