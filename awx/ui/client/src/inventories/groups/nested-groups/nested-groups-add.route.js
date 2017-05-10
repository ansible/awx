import { N_ } from '../../../i18n';

export default {
    name: "inventories.edit.groups.edit.nested_groups.add",
    url: "/add",
    ncyBreadcrumb: {
        parent: "inventories.edit.groups.edit.nested_groups",
        label: N_("CREATE GROUP")
    },
    views: {
        'nestedGroupForm@inventories': {
            templateProvider: function(GenerateForm, GroupForm) {
                let form = GroupForm;
                return GenerateForm.buildHTML(form, {
                    mode: 'add',
                    related: false
                });
            },
            controller: 'GroupAddController'
        }
    }
};
