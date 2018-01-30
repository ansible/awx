import { templateUrl } from '../shared/template-url/template-url.factory';
import CapacityAdjuster from './capacity-adjuster/capacity-adjuster.directive';
import CapacityBar from './capacity-bar/main';
import instanceGroupsMultiselect from '../shared/instance-groups-multiselect/instance-groups.directive';
import instanceGroupsModal from '../shared/instance-groups-multiselect/instance-groups-modal/instance-groups-modal.directive';

import AddEditTemplate from './add-edit/add-edit-instance-groups.view.html';
import AddInstanceGroupController from './add-edit/add-instance-group.controller';
import EditInstanceGroupController from './add-edit/edit-instance-group.controller';
import InstanceListPolicyTemplate from './add-edit/instance-list-policy.partial.html';
import InstanceListPolicyController from './add-edit/instance-list-policy.controller.js';

import InstanceGroupsTemplate from './list/instance-groups-list.partial.html';
import InstanceGroupsListController from './list/instance-groups-list.controller';

import InstancesTemplate from './instances/instances-list.partial.html';
import InstanceListController from './instances/instances.controller';

import JobsTemplate from './jobs/jobs-list.partial.html';
import InstanceGroupJobsListController from './jobs/jobs.controller';
import InstanceJobsListController from './instances/instance-jobs/instance-jobs.controller';

import InstanceModalTemplate from './instances/instance-modal.partial.html';
import InstanceModalController from './instances/instance-modal.controller.js';

import list from './instance-groups.list';
import service from './instance-groups.service';

import InstanceGroupsStrings from './instance-groups.strings';
import JobStrings from './jobs/jobs.strings';

const MODULE_NAME = 'instanceGroups';

function InstanceGroupsResolve ($q, $stateParams, InstanceGroup, Instance) {
    const instanceGroupId = $stateParams.instance_group_id;
    const instanceId = $stateParams.instance_id;
    let promises = {};

    if (!instanceGroupId && !instanceId) {
        promises.instanceGroup = new InstanceGroup(['get', 'options']);
        promises.instance = new Instance(['get', 'options']);

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
        views: {
            'add@instanceGroups': {
                templateUrl: AddEditTemplate,
                controller: AddInstanceGroupController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve
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
                templateUrl: InstanceListPolicyTemplate,
                controller: InstanceListPolicyController,
                controllerAs: 'vm'
            }
        },
        resolvedModels: InstanceGroupsResolve
    });

    $stateExtender.addState({
        name: 'instanceGroups.edit',
        route: '/:instance_group_id',
        ncyBreadcrumb: {
            label: strings.get('state.EDIT_BREADCRUMB_LABEL')
        },
        views: {
            'edit@instanceGroups': {
                templateUrl: AddEditTemplate,
                controller: EditInstanceGroupController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve
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
                templateUrl: InstanceListPolicyTemplate,
                controller: InstanceListPolicyController,
                controllerAs: 'vm'
            }
        },
        resolvedModels: InstanceGroupsResolve
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

    $stateExtender.addState({
        name: 'instanceGroups.instanceJobs',
        url: '/:instance_group_id/instances/:instance_id/jobs',
        ncyBreadcrumb: {
            parent: 'instanceGroups.instances',
            label: ComponentsStrings.get('layout.JOBS')
        },
        views: {
            'instanceJobs@instanceGroups': {
                templateUrl: JobsTemplate,
                controller: 'InstanceJobsListController',
                controllerAs: 'vm'
            },
        },
        params: {
            job_search: {
                value: {
                    page_size: '10',
                    order_by: '-finished'
                },
                dynamic: true
            },
        },
        resolvedModels: InstanceGroupsResolve
    });

    $stateExtender.addState({
        name: 'instanceGroups.jobs',
        url: '/:instance_group_id/jobs',
        ncyBreadcrumb: {
            parent: 'instanceGroups.edit',
            label: ComponentsStrings.get('layout.JOBS')
        },
        params: {
            job_search: {
                value: {
                    page_size: '10',
                    order_by: '-finished'
                },
                dynamic: true
            }
        },
        views: {
            'jobs@instanceGroups': {
                templateUrl: JobsTemplate,
                controller: 'InstanceGroupJobsListController',
                controllerAs: 'vm'
            },
        },
        resolve: {
            resolvedModels: InstanceGroupsResolve
        }
    });
}

InstanceGroupsRun.$inject = [
    '$stateExtender',
    'InstanceGroupsStrings',
    'ComponentsStrings'
];

angular.module(MODULE_NAME, [CapacityBar.name])
    .service('InstanceGroupsService', service)
    .factory('InstanceGroupList', list)
    .controller('InstanceGroupsListController', InstanceGroupsListController)
    .controller('InstanceGroupJobsListController', InstanceGroupJobsListController)
    .controller('InstanceListController', InstanceListController)
    .controller('InstanceJobsListController', InstanceJobsListController)
    .directive('instanceGroupsMultiselect', instanceGroupsMultiselect)
    .directive('instanceGroupsModal', instanceGroupsModal)
    .directive('capacityAdjuster', CapacityAdjuster)
    .service('InstanceGroupsStrings', InstanceGroupsStrings)
    .service('JobStrings', JobStrings)
    .run(InstanceGroupsRun);

export default MODULE_NAME;
