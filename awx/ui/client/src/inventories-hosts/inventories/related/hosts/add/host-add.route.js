import { N_ } from '../../../../../i18n';

export default {
    name: "inventories.edit.hosts.add",
    url: "/add",
    ncyBreadcrumb: {
        parent: "inventories.edit.hosts",
        label: N_("CREATE HOST")
    },
    views: {
        'hostForm@inventories': {
            templateProvider: function(GenerateForm, RelatedHostsFormDefinition) {
                let form = RelatedHostsFormDefinition;
                return GenerateForm.buildHTML(form, {
                    mode: 'add',
                    related: false
                });
            },
            controller: 'RelatedHostAddController'
        }
    },
};
