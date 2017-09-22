import { templateUrl } from '../../../shared/template-url/template-url.factory';

export default {
    name: 'instanceGroups.instances.list.job',
    url: '/:instance_id',
    abstract: true,
    ncyBreadcrumb: {
        skip: true
    },
    views: {
        'instanceJobs@instanceGroups': {
            templateUrl: templateUrl('./instance-groups/instances/instance-jobs/instance-jobs'),
            controller: function($scope, $rootScope, instance) {
                $scope.instanceName = instance.hostname;
                $scope.instanceCapacity = instance.consumed_capacity;
                $scope.instanceTotalCapacity = instance.capacity;
                $scope.instanceJobsRunning = instance.jobs_running;
                $rootScope.breadcrumb.instance_name = instance.hostname;
            }
        }
    },
    resolve: {
        instance: ['GetBasePath', 'Rest', 'ProcessErrors', '$stateParams', function(GetBasePath, Rest, ProcessErrors, $stateParams) {
        let url = GetBasePath('instances') + $stateParams.instance_id;
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
