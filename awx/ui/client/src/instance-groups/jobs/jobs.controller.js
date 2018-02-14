
function InstanceGroupJobsController ($scope, $filter, $state, model, strings, jobStrings, InstanceGroup) {
    const vm = this || {};
    let { instanceGroup } = model;
    const instance_group_id = instanceGroup.get('id');

    init();

    function init(){
        vm.strings = strings;
        vm.jobStrings = jobStrings;
        vm.queryset = { page_size: '10', order_by: '-finished', instance_group_id: instance_group_id };
        vm.jobs = instanceGroup.get('related.jobs.results');
        vm.dataset = instanceGroup.get('related.jobs');
        vm.count = instanceGroup.get('related.jobs.count');
        vm.panelTitle = instanceGroup.get('name');

        vm.tab = {
            details: {
                _go: 'instanceGroups.edit',
                _params: { instance_group_id },
                _label: strings.get('tab.DETAILS')
            },
            instances: {
                _go: 'instanceGroups.instances',
                _params: { instance_group_id },
                _label: strings.get('tab.INSTANCES')
            },
            jobs: {
                _active: true,
                _label: strings.get('tab.JOBS')
            }
        };
    }

    vm.getTime = function(time) {
        let val = "";
        if (time) {
            val += $filter('longDate')(time);
        }
        if (val === "") {
            val = undefined;
        }
        return val;
    };

    $scope.isSuccessful = function (status) {
        return (status === "successful");
    };

    vm.viewjobResults = function(job) {
        var goTojobResults = function(state) {
            $state.go(state, { id: job.id }, { reload: true });
        };
        switch (job.type) {
            case 'job':
                goTojobResults('jobResult');
                break;
            case 'ad_hoc_command':
                goTojobResults('adHocJobStdout');
                break;
            case 'system_job':
                goTojobResults('managementJobStdout');
                break;
            case 'project_update':
                goTojobResults('scmUpdateStdout');
                break;
            case 'inventory_update':
                goTojobResults('inventorySyncStdout');
                break;
            case 'workflow_job':
                goTojobResults('workflowResults');
                break;
        }
    };

    $scope.$on('ws-jobs', () => {
        new InstanceGroup(['get', 'options'], [instance_group_id, instance_group_id])
            .then((instance_group) =>  {
                return instance_group.extend('get', 'jobs', {params: {page_size: "10", order_by: "-finished"}});
            })
            .then((instance_group) => {
                instanceGroup = instance_group;
                init();
            });
    });

}

InstanceGroupJobsController.$inject = [
    '$scope',
    '$filter',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings',
    'JobStrings',
    'InstanceGroupModel'
];

export default InstanceGroupJobsController;