
import AddController from './add-inventory-scripts.controller';
import EditController from './edit-inventory-scripts.controller';
import ListController from './list-inventory-scripts.controller';
import InventoryScriptsStrings from './inventory-scripts.strings';

const MODULE_NAME = 'at.features.inventoryScripts';
const addEditTemplate = require('~features/inventory-scripts/add-edit-inventory-scripts.view.html');
const listTemplate = require('~features/inventory-scripts/list-inventory-scripts.view.html');
const indexTemplate = require('~features/inventory-scripts/index.view.html');

function InventoryScriptsRun ($stateExtender, strings) {
    $stateExtender.addState({
        name: 'inventoryScripts',
        route: '/inventory_scripts',
        ncyBreadcrumb: {
            label: strings.get('state.LIST_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'custom_inventory_script'
        },
        views: {
            '@': {
                templateUrl: indexTemplate,
            },
            'list@inventoryScripts': {
                templateUrl: listTemplate,
                controller: ListController,
                controllerAs: 'vm'
            }
        },
        searchPrefix: 'inventory_script',
        resolve: {
            inventoryScriptModel: [
                'InventoryScriptModel',
                (InventoryScript) => new InventoryScript(['options'])
            ],
            Dataset: [
                'inventoryScriptModel',
                '$stateParams',
                (inventoryScriptModel, $stateParams) => inventoryScriptModel.http.get({
                    params: $stateParams.inventory_script_search
                })
            ],
        }
    });

    $stateExtender.addState({
        name: 'inventoryScripts.add',
        route: '/add',
        ncyBreadcrumb: {
            label: strings.get('state.ADD_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'custom_inventory_script'
        },
        views: {
            'add@inventoryScripts': {
                templateUrl: addEditTemplate,
                controller: AddController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            models: [
                'InventoryScriptModel',
                'OrganizationModel',
                '$q',
                (InventoryScript, Organization, $q) => $q.all({
                    inventoryScript: new InventoryScript('options'),
                    organization: new Organization()
                })
            ]
        }
    });

    $stateExtender.addState({
        name: 'inventoryScripts.edit',
        route: '/:inventory_script_id',
        ncyBreadcrumb: {
            label: strings.get('state.EDIT_BREADCRUMB_LABEL')
        },
        data: {
            activityStream: true,
            activityStreamTarget: 'custom_inventory_script',
            activityStreamId: 'inventory_script_id'
        },
        views: {
            'edit@inventoryScripts': {
                templateUrl: addEditTemplate,
                controller: EditController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            models: [
                'InventoryScriptModel',
                'OrganizationModel',
                '$q',
                '$state',
                '$transition$',
                (InventoryScript, Organization, $q, $state, $transition$) => {
                    const invScriptId = $transition$.params().inventory_script_id;

                    return new InventoryScript(['get', 'options'], [invScriptId, invScriptId])
                        .then(inventoryScript => {
                            const orgId = inventoryScript.get('organization');

                            return new Organization('get', orgId)
                                .then(organization => ({ inventoryScript, organization }));
                        });
                }
            ]
        }
    });

    $stateExtender.addState({
        name: 'inventoryScripts.add.organization',
        url: '/organization?selected',
        searchPrefix: 'organization',
        params: {
            organization_search: {
                value: {
                    page_size: 5,
                    order_by: 'name'
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'organizations',
            formChildState: true
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {
            'organization@inventoryScripts.add': {
                templateProvider: (ListDefinition, generateList) => {
                    const html = generateList.build({
                        mode: 'lookup',
                        list: ListDefinition,
                        input_type: 'radio'
                    });

                    return `<lookup-modal>${html}</lookup-modal>`;
                }
            }
        },
        resolve: {
            ListDefinition: ['OrganizationList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => qs.search(
                    GetBasePath('organizations'),
                    $stateParams[`${list.iterator}_search`]
                )
            ]
        },
        onExit ($state) {
            if ($state.transition) {
                $('#form-modal').modal('hide');
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }
        }
    });

    $stateExtender.addState({
        name: 'inventoryScripts.edit.organization',
        url: '/organization?selected',
        searchPrefix: 'organization',
        params: {
            organization_search: {
                value: {
                    page_size: 5,
                    order_by: 'name'
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'organizations',
            formChildState: true
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {
            'organization@inventoryScripts.edit': {
                templateProvider: (ListDefinition, generateList) => {
                    const html = generateList.build({
                        mode: 'lookup',
                        list: ListDefinition,
                        input_type: 'radio'
                    });

                    return `<lookup-modal>${html}</lookup-modal>`;
                }
            }
        },
        resolve: {
            ListDefinition: ['OrganizationList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
                (list, qs, $stateParams, GetBasePath) => qs.search(
                    GetBasePath('organizations'),
                    $stateParams[`${list.iterator}_search`]
                )
            ]
        },
        onExit ($state) {
            if ($state.transition) {
                $('#form-modal').modal('hide');
                $('.modal-backdrop').remove();
                $('body').removeClass('modal-open');
            }
        }
    });
}

InventoryScriptsRun.$inject = [
    '$stateExtender',
    'InventoryScriptsStrings'
];

angular
    .module(MODULE_NAME, [])
    .service('InventoryScriptsStrings', InventoryScriptsStrings)
    .run(InventoryScriptsRun);

export default MODULE_NAME;
