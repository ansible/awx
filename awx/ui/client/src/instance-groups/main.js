import InstanceGroupsList from './list/instance-groups-list.controller';
import instanceGroupsMultiselect from '../shared/instance-groups-multiselect/instance-groups.directive';
import instanceGroupsModal from '../shared/instance-groups-multiselect/instance-groups-modal/instance-groups-modal.directive';
import instanceGroupsRoute from './instance-groups.route';
import instancesListRoute from './instances/instances-list.route';
import JobsList from './jobs/jobs.list';
import jobsListRoute from './jobs/jobs-list.route';
import JobsListController from './jobs/jobs.controller';
import InstanceList from './instances/instances.list';
import instancesRoute from './instances/instances.route';
import InstanceListController from './instances/instances.controller';
import InstanceJobsList from './instances/instance-jobs/instance-jobs.list';
import instanceJobsRoute from './instances/instance-jobs/instance-jobs.route';
import instanceJobsListRoute from './instances/instance-jobs/instance-jobs-list.route';
import InstanceJobsController from './instances/instance-jobs/instance-jobs.controller';
import CapacityBar from './capacity-bar/main';
import list from './instance-groups.list';
import service from './instance-groups.service';

export default
angular.module('instanceGroups', [CapacityBar.name])
    .service('InstanceGroupsService', service)
    .factory('InstanceGroupList', list)
    .factory('JobsList', JobsList)
    .factory('InstanceList', InstanceList)
    .factory('InstanceJobsList', InstanceJobsList)
    .controller('InstanceGroupsList', InstanceGroupsList)
    .controller('JobsListController', JobsListController)
    .controller('InstanceListController', InstanceListController)
    .controller('InstanceJobsController', InstanceJobsController)
    .directive('instanceGroupsMultiselect', instanceGroupsMultiselect)
    .directive('instanceGroupsModal', instanceGroupsModal)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateExtender = $stateExtenderProvider.$get();


            function generateInstanceGroupsStates() {
                return new Promise((resolve) => {
                    resolve({
                        states: [
                            stateExtender.buildDefinition(instanceGroupsRoute),
                            stateExtender.buildDefinition(instancesRoute),
                            stateExtender.buildDefinition(instancesListRoute),
                            stateExtender.buildDefinition(jobsListRoute),
                            stateExtender.buildDefinition(instanceJobsRoute),
                            stateExtender.buildDefinition(instanceJobsListRoute)
                        ]
                    });
                });
            }

            $stateProvider.state({
                name: 'instanceGroups',
                url: '/instance_groups',
                lazyLoad: () => generateInstanceGroupsStates()
            });
        }]);
