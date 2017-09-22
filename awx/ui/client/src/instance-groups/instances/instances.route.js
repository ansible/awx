import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'instanceGroups.instances',
    url: '/:instance_group_id',
    abstract: true,
    views: {
        'instances@instanceGroups': {
            templateUrl: templateUrl('./instance-groups/instance-group'),
            controller: function($scope, $rootScope, instanceGroup) {
                $scope.instanceGroupName = instanceGroup.name;
                $scope.instanceGroupCapacity = instanceGroup.consumed_capacity;
                $scope.instanceGroupTotalCapacity = instanceGroup.capacity;
                $scope.instanceGroupJobsRunning = instanceGroup.jobs_running;
                $rootScope.breadcrumb.instance_group_name = instanceGroup.name;
            }
        }
    },
    resolve: {
        instanceGroup: ['GetBasePath', 'Rest', 'ProcessErrors', '$stateParams', function(GetBasePath, Rest, ProcessErrors, $stateParams) {
            let url = GetBasePath('instance_groups') + $stateParams.instance_group_id;
            Rest.setUrl(url);
            return Rest.get()
                .then(({data}) => {
                    return data;
                })
                .catch(({data, status}) => {
                    ProcessErrors(null, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to get instance groups info. GET returned status: ' + status
                    });
                });
        }]
    }
};
