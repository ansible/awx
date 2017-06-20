import { N_ } from '../../../../../i18n';

export default {
    name: "inventories.edit.groups.add",
    url: "/add",
    ncyBreadcrumb: {
        parent: "inventories.edit.groups",
        label: N_("CREATE GROUP")
    },
    views: {
        'groupForm@inventories': {
            templateProvider: function(GenerateForm, GroupForm) {
                let form = GroupForm;
                return GenerateForm.buildHTML(form, {
                    mode: 'add',
                    related: false
                });
            },
            controller: 'GroupAddController'
        }
    },
};
