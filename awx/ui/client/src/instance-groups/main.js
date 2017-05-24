import InstanceGroupsList from './list/instance-groups-list.controller';
import list from './instance-groups.list';
import service from './instance-groups.service';
import { N_ } from '../i18n';

export default
angular.module('instanceGroups', [])
    .factory('InstanceGroupList', list)
    .service('InstanceGroupsService', service)
    .controller('InstanceGroupsList', InstanceGroupsList)
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
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'instanceGroup'
                    },
                    ncyBreadcrumb: {
                        parent: 'setup',
                        label: N_('INSTANCE GROUPS')
                    }
                })
            });

        }
    ]);