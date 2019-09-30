import {
    templateUrl
} from '../shared/template-url/template-url.factory';
import CapacityAdjuster from './capacity-adjuster/capacity-adjuster.directive';
import AddContainerGroup from './container-groups/add-container-group.view.html';
import EditContainerGroupController from './container-groups/edit-container-group.controller';
import AddContainerGroupController from './container-groups/add-container-group.controller';
import CapacityBar from './capacity-bar/capacity-bar.directive';
import instanceGroupsMultiselect from '../shared/instance-groups-multiselect/instance-groups.directive';
import instanceGroupsModal from '../shared/instance-groups-multiselect/instance-groups-modal/instance-groups-modal.directive';

import AddEditTemplate from './add-edit/add-edit-instance-groups.view.html';
import AddInstanceGroupController from './add-edit/add-instance-group.controller';
import EditInstanceGroupController from './add-edit/edit-instance-group.controller';

import InstanceGroupsTemplate from './list/instance-groups-list.partial.html';
import InstanceGroupsListController from './list/instance-groups-list.controller';

import InstancesTemplate from './instances/instances-list.partial.html';
import InstanceListController from './instances/instances.controller';

import InstanceModalTemplate from './instances/instance-modal.partial.html';
import InstanceModalController from './instances/instance-modal.controller.js';

import list from './instance-groups.list';
import service from './instance-groups.service';

import InstanceGroupsStrings from './instance-groups.strings';

import {instanceGroupJobsRoute, containerGroupJobsRoute} from '~features/jobs/routes/instanceGroupJobs.route.js';
import instanceJobsRoute from '~features/jobs/routes/instanceJobs.route.js';


const MODULE_NAME = 'instanceGroups';

function InstanceGroupsResolve($q, $stateParams, InstanceGroup, Credential, Instance, ProcessErrors, strings) {
    const instanceGroupId = $stateParams.instance_group_id;
    const instanceId = $stateParams.instance_id;
    let promises = {};

    if (!instanceGroupId && !instanceId) {
        promises.instanceGroup = new InstanceGroup(['get', 'options']);
        promises.credential = new Credential(['get', 'options']);
        return $q.all(promises);
    }

    if (instanceGroupId && instanceId) {
        promises.instance = new Instance(['get', 'options'], [instanceId, instanceId])
        .then((instance) => instance.extend('get', 'jobs', {
            params: {
                page_size: "10",
                order_by: "-finished"
            }
        }));
        return $q.all(promises);
    }

    promises.instanceGroup = new InstanceGroup(['get', 'options'], [instanceGroupId, instanceGroupId])
    .then((instanceGroup) => instanceGroup.extend('get', 'jobs', {
        params: {
            page_size: "10",
            order_by: "-finished"
        }
    }))
    .then((instanceGroup) => instanceGroup.extend('get', 'instances'));

    promises.credential = new Credential();

    return $q.all(promises)
        .then(models => models)
        .catch(({
            data,
            status,
            config
        }) => {
            ProcessErrors(null, data, status, null, {
                hdr: strings.get('error.HEADER'),
                msg: strings.get('error.CALL', {
                    path: `${config.url}`,
                    status
                })
            });
            return $q.reject();
        });
}

InstanceGroupsResolve.$inject = [
    '$q',
    '$stateParams',
    'InstanceGroupModel',
    'CredentialModel',
    'InstanceModel',
    'ProcessErrors',
    'InstanceGroupsStrings'
];

function InstanceGroupsRun($stateExtender, strings) {
    $stateExtender.addState({
        name: 'instanceGroups',
        url: '/instance_groups',
        searchPrefix: 'instance_group',
        ncyBreadcrumb: {
            label: strings.get('state.INSTANCE_GROUPS_BREADCRUMB_LABEL')
        },
        params: {
            instance_group_search: {
                value: {
                    page_size: '10',
                    order_by: 'name'
                },
                dynamic: true
            }
        },
        data: {
            alwaysShowRefreshButton: true,
        },
        views: {
            '@': {
                templateUrl: templateUrl('./instance-groups/instance-groups'),
            },
            'list@instanceGroups': {
                templateUrl: InstanceGroupsTemplate,
                controller: 'InstanceGroupsListController',
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve,
            Dataset: ['InstanceGroupList', 'QuerySet', '$stateParams', 'GetBasePath',
                function (list, qs, $stateParams, GetBasePath) {
                    let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                    return qs.search(path, $stateParams[`${list.iterator}_search`]);
                }
            ]
        }
    });

    $stateExtender.addState({
        name: 'instanceGroups.add',
        url: '/add',
        ncyBreadcrumb: {
            label: strings.get('state.ADD_BREADCRUMB_LABEL')
        },
        params: {
            instance_search: {
                value: {
                    order_by: 'hostname',
                    page_size: '10'
                }
            }
        },
        views: {
            'add@instanceGroups': {
                templateUrl: AddEditTemplate,
                controller: AddInstanceGroupController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve,
            Dataset: [
                '$stateParams',
                'GetBasePath',
                'QuerySet',
                ($stateParams, GetBasePath, qs) => {
                    const searchParams = $stateParams.instance_search;
                    const searchPath = GetBasePath('instances');
                    return qs.search(searchPath, searchParams);
                }
            ]
        }
    });
    $stateExtender.addState({
        name: 'instanceGroups.addContainerGroup',
        url: '/container_group',
        views: {
            'addContainerGroup@instanceGroups': {
                templateUrl: AddContainerGroup,
                controller: AddContainerGroupController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve,
            DataSet: ['Rest', 'GetBasePath', (Rest, GetBasePath) => {
                Rest.setUrl(`${GetBasePath('instance_groups')}`);
                return Rest.options();
            }]
        },
        ncyBreadcrumb: {
            label: strings.get('state.ADD_CONTAINER_GROUP_BREADCRUMB_LABEL')
        },
    });

    $stateExtender.addState({
        name: 'instanceGroups.addContainerGroup.credentials',
        url: '/credential?selected',
        searchPrefix: 'credential',
        params: {
            credential_search: {
                value: {
                    credential_type__kind: 'kubernetes',
                    order_by: 'name',
                    page_size: 5,
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'credentials',
            formChildState: true
        },
        ncyBreadcrumb: {
            skip: true
        },
        views: {
            'credentials@instanceGroups.addContainerGroup': {
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
            ListDefinition: ['CredentialList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', (list, qs, $stateParams, GetBasePath) => {


                const searchPath = GetBasePath('credentials');
                return qs.search(
                    searchPath,
                    $stateParams[`${list.iterator}_search`]
                );
            }]
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
        name: 'instanceGroups.editContainerGroup',
        url: '/container_group/:instance_group_id',
        views: {
            'editContainerGroup@instanceGroups': {
                templateUrl: AddContainerGroup,
                controller: EditContainerGroupController,
                controllerAs: 'vm'
            }
        },

        resolve: {
            resolvedModels: InstanceGroupsResolve,
            EditContainerGroupDataset: ['GetBasePath', 'QuerySet', '$stateParams',
                function (GetBasePath, qs, $stateParams) {
                let path = `${GetBasePath('instance_groups')}${$stateParams.instance_group_id}`;
                    return qs.search(path, $stateParams);
                }
            ],
        },
        ncyBreadcrumb: {
            label: '{{breadcrumb.instance_group_name}}'
        },
    });

    $stateExtender.addState({
        name: 'instanceGroups.editContainerGroup.credentials',
        url: '/credential?selected',
        searchPrefix: 'credential',
        params: {
            credential_search: {
                value: {
                    credential_type__kind: 'kubernetes',
                    order_by: 'name',
                    page_size: 5,
                },
                dynamic: true,
                squash: ''
            }
        },
        data: {
            basePath: 'credentials',
            formChildState: true
        },
        views: {
            'credentials@instanceGroups.editContainerGroup': {
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
            ListDefinition: ['CredentialList', list => list],
            Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath', (list, qs, $stateParams, GetBasePath) => {
                const searchPath = GetBasePath('credentials');
                return qs.search(
                    searchPath,
                    $stateParams[`${list.iterator}_search`]
                );
            }]
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
        name: 'instanceGroups.edit',
        route: '/:instance_group_id',
        ncyBreadcrumb: {
            label: '{{breadcrumb.instance_group_name}}'
        },
        params: {
            instance_search: {
                value: {
                    order_by: 'hostname',
                    page_size: '10'
                }
            }
        },
        views: {
            'edit@instanceGroups': {
                templateUrl: AddEditTemplate,
                controller: EditInstanceGroupController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve,
            Dataset: [
                '$stateParams',
                'GetBasePath',
                'QuerySet',
                ($stateParams, GetBasePath, qs) => {
                    const searchParams = $stateParams.instance_search;
                    const searchPath = GetBasePath('instances');
                    return qs.search(searchPath, searchParams);
                }
            ]
        }
    });

    $stateExtender.addState({
        name: 'instanceGroups.instances',
        url: '/:instance_group_id/instances',
        searchPrefix: 'instance',
        ncyBreadcrumb: {
            parent: 'instanceGroups.edit',
            label: strings.get('state.INSTANCES_BREADCRUMB_LABEL')
        },
        params: {
            instance_search: {
                value: {
                    order_by: 'hostname',
                    page_size: '10'
                },
                dynamic: true
            }
        },
        views: {
            'instances@instanceGroups': {
                templateUrl: InstancesTemplate,
                controller: 'InstanceListController',
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve,
            Dataset: ['GetBasePath', 'QuerySet', '$stateParams',
                function (GetBasePath, qs, $stateParams) {
                    let path = `${GetBasePath('instance_groups')}${$stateParams.instance_group_id}/instances`;
                    return qs.search(path, $stateParams[`instance_search`]);
                }
            ],
        }
    });

    $stateExtender.addState({
        name: 'instanceGroups.instances.modal',
        abstract: true,
        ncyBreadcrumb: {
            skip: true,
        },
        views: {
            "modal": {
                template: `<div class="Modal-backdrop"></div>
                <div class="Modal-holder" ui-view="modal" autoscroll="false"></div>`,
            }
        }
    });

    $stateExtender.addState({
        name: 'instanceGroups.instances.modal.add',
        url: '/add',
        ncyBreadcrumb: {
            skip: true,
        },
        searchPrefix: 'add_instance',
        params: {
            add_instance_search: {
                value: {
                    page_size: '10',
                    order_by: 'hostname'
                },
                dynamic: true
            }
        },
        views: {
            "modal": {
                templateUrl: InstanceModalTemplate,
                controller: InstanceModalController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve,
            Dataset: ['GetBasePath', 'QuerySet', '$stateParams',
                function (GetBasePath, qs, $stateParams) {
                    let path = `${GetBasePath('instances')}`;
                    return qs.search(path, $stateParams[`add_instance_search`]);
                }
            ],
            routeData: [function () {
                return "instanceGroups.instances";
            }]
        }
    });

    $stateExtender.addState(instanceJobsRoute);
    $stateExtender.addState(instanceGroupJobsRoute);
    $stateExtender.addState(containerGroupJobsRoute);
}

InstanceGroupsRun.$inject = [
    '$stateExtender',
    'InstanceGroupsStrings',
    'Rest'
];

angular.module(MODULE_NAME, [])
    .service('InstanceGroupsService', service)
    .factory('InstanceGroupList', list)
    .controller('InstanceGroupsListController', InstanceGroupsListController)
    .controller('InstanceListController', InstanceListController)
    .directive('instanceGroupsMultiselect', instanceGroupsMultiselect)
    .directive('instanceGroupsModal', instanceGroupsModal)
    .directive('capacityAdjuster', CapacityAdjuster)
    .directive('capacityBar', CapacityBar)
    .service('InstanceGroupsStrings', InstanceGroupsStrings)
    .run(InstanceGroupsRun);

export default MODULE_NAME;
