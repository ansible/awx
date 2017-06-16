import InstanceGroupsList from './list/instance-groups-list.controller';
import instanceGroupsMultiselect from './instance-groups-multiselect/instance-groups.directive';
import instanceGroupsModal from './instance-groups-multiselect/instance-groups-modal/instance-groups-modal.directive';
import list from './instance-groups.list';
import service from './instance-groups.service';
import { N_ } from '../i18n';

export default
angular.module('instanceGroups', [])
    .service('InstanceGroupsService', service)
    .factory('InstanceGroupList', list)
    .controller('InstanceGroupsList', InstanceGroupsList)
    .directive('instanceGroupsMultiselect', instanceGroupsMultiselect)
    .directive('instanceGroupsModal', instanceGroupsModal)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();

            $stateProvider.state({
                name: 'instanceGroups',
                url: '/instance_groups',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'instanceGroups',
                    list: 'InstanceGroupList',
                    controllers: {
                        list: 'InstanceGroupsList'
                    },
                    ncyBreadcrumb: {
                        parent: 'setup',
                        label: N_('INSTANCE GROUPS')
                    }
                })
            });
        }
    ]);