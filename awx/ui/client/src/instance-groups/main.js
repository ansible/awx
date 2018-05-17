import { templateUrl } from '../shared/template-url/template-url.factory';
import CapacityAdjuster from './capacity-adjuster/capacity-adjuster.directive';
import CapacityBar from './capacity-bar/capacity-bar.directive';
import instanceGroupsMultiselect from '../shared/instance-groups-multiselect/instance-groups.directive';
import instanceGroupsModal from '../shared/instance-groups-multiselect/instance-groups-modal/instance-groups-modal.directive';

import AddEditTemplate from './add-edit/add-edit-instance-groups.view.html';
import AddInstanceGroupController from './add-edit/add-instance-group.controller';
import EditInstanceGroupController from './add-edit/edit-instance-group.controller';
import InstanceListPolicy from './add-edit/instance-list-policy.directive.js';

import InstanceGroupsTemplate from './list/instance-groups-list.partial.html';
import InstanceGroupsListController from './list/instance-groups-list.controller';

import InstancesTemplate from './instances/instances-list.partial.html';
import InstanceListController from './instances/instances.controller';

import InstanceModalTemplate from './instances/instance-modal.partial.html';
import InstanceModalController from './instances/instance-modal.controller.js';

import list from './instance-groups.list';
import service from './instance-groups.service';

import InstanceGroupsStrings from './instance-groups.strings';

import instanceGroupJobsRoute from '~features/jobs/routes/instanceGroupJobs.route.js';
import instanceJobsRoute from '~features/jobs/routes/instanceJobs.route.js';

const MODULE_NAME = 'instanceGroups';

function InstanceGroupsResolve ($q, $stateParams, InstanceGroup, Instance) {
    const instanceGroupId = $stateParams.instance_group_id;
    const instanceId = $stateParams.instance_id;
    let promises = {};

    if (!instanceGroupId && !instanceId) {
        promises.instanceGroup = new InstanceGroup(['get', 'options']);
        return $q.all(promises);
    }

    if (instanceGroupId && instanceId) {
        promises.instance = new Instance(['get', 'options'], [instanceId, instanceId])
            .then((instance) => instance.extend('get', 'jobs', {params: {page_size: "10", order_by: "-finished"}}));
        return $q.all(promises);
    }

    promises.instanceGroup = new InstanceGroup(['get', 'options'], [instanceGroupId, instanceGroupId])
            .then((instanceGroup) =>  instanceGroup.extend('get', 'jobs', {params: {page_size: "10", order_by: "-finished"}}))
            .then((instanceGroup) =>  instanceGroup.extend('get', 'instances'));
    promises.instance = new Instance('get');


    return $q.all(promises)
        .then(models => models);
}

InstanceGroupsResolve.$inject = [
    '$q',
    '$stateParams',
    'InstanceGroupModel',
    'InstanceModel'
];

function InstanceGroupsRun ($stateExtender, strings, ComponentsStrings) {
    $stateExtender.addState({
        name: 'instanceGroups',
        url: '/instance_groups',
        searchPrefix: 'instance_group',
        ncyBreadcrumb: {
            label: ComponentsStrings.get('layout.INSTANCE_GROUPS')
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
                function(list, qs, $stateParams, GetBasePath) {
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
        name: 'instanceGroups.add.modal',
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
        name: 'instanceGroups.add.modal.instances',
        ncyBreadcrumb: {
            skip: true,
        },
        views: {
            "modal": {
                template: '<instance-list-policy></instance-list-policy>',
            }
        }
    });

    $stateExtender.addState({
        name: 'instanceGroups.edit',
        route: '/:instance_group_id',
        ncyBreadcrumb: {
            label: strings.get('state.EDIT_BREADCRUMB_LABEL')
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
        name: 'instanceGroups.edit.modal',
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
        name: 'instanceGroups.edit.modal.instances',
        ncyBreadcrumb: {
            skip: true,
        },
        views: {
            "modal": {
                template: '<instance-list-policy></instance-list-policy>',
            }
        }
    });

    $stateExtender.addState({
        name: 'instanceGroups.instances',
        url: '/:instance_group_id/instances',
        ncyBreadcrumb: {
            parent: 'instanceGroups.edit',
            label: ComponentsStrings.get('layout.INSTANCES')
        },
        params: {
            instance_search: {
                value: {
                    page_size: '10',
                    order_by: 'hostname'
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
            resolvedModels: InstanceGroupsResolve
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
        ncyBreadcrumb: {
            skip: true,
        },
        views: {
            "modal": {
                templateUrl: InstanceModalTemplate,
                controller: InstanceModalController,
                controllerAs: 'vm'
            }
        },
        resolvedModels: InstanceGroupsResolve
    });

    $stateExtender.addState(instanceJobsRoute);
    $stateExtender.addState(instanceGroupJobsRoute);
}

InstanceGroupsRun.$inject = [
    '$stateExtender',
    'InstanceGroupsStrings',
    'ComponentsStrings'
];

angular.module(MODULE_NAME, [])
    .service('InstanceGroupsService', service)
    .factory('InstanceGroupList', list)
    .controller('InstanceGroupsListController', InstanceGroupsListController)
    .controller('InstanceListController', InstanceListController)
    .directive('instanceListPolicy', InstanceListPolicy)
    .directive('instanceGroupsMultiselect', instanceGroupsMultiselect)
    .directive('instanceGroupsModal', instanceGroupsModal)
    .directive('capacityAdjuster', CapacityAdjuster)
    .directive('capacityBar', CapacityBar)
    .service('InstanceGroupsStrings', InstanceGroupsStrings)
    .run(InstanceGroupsRun);

export default MODULE_NAME;
