import { N_ } from '../../../../../../i18n';

export default {
    name: "inventories.edit.groups.edit.nested_groups.add",
    url: "/add",
    ncyBreadcrumb: {
        parent: "inventories.edit.groups.edit.nested_groups",
        label: N_("CREATE GROUP")
    },
    views: {
        'nestedGroupForm@inventories': {
            templateProvider: function(GenerateForm, NestedGroupForm) {
                let form = NestedGroupForm;
                return GenerateForm.buildHTML(form, {
                    mode: 'add',
                    related: false
                });
            },
            controller: 'NestedGroupsAddController'
        }
    },
    resolve: {
        canAdd: ['rbacUiControlService', '$state', 'GetBasePath', '$stateParams', function(rbacUiControlService, $state, GetBasePath, $stateParams) {
            return rbacUiControlService.canAdd(GetBasePath('inventory') + $stateParams.inventory_id + "/groups")
                .then(function(res) {
                    return res.canAdd;
                })
                .catch(function() {
                    return false;
                });
        }]
    }
};
