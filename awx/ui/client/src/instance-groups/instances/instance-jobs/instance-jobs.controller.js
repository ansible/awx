
function InstanceJobsController ($scope, $filter, $state, model, strings, jobStrings) {
    const vm = this || {};
    const { instance } = model;

    init();

    function init(){
        vm.strings = strings;
        vm.jobStrings = jobStrings;
        vm.queryset = { page_size: '10', order_by: '-finished'};
        vm.jobs = instance.get('related.jobs.results');
        vm.dataset = instance.get('related.jobs');
        vm.count = instance.get('related.jobs.count');
        vm.panelTitle = `${jobStrings.get('list.PANEL_TITLE')} | ${instance.get('hostname')}`;

        vm.tab = {
            details: {_hide: true},
            instances: {_hide: true},
            jobs: {_hide: true}
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

    $scope.viewjobResults = function(job) {
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

}

InstanceJobsController.$inject = [
    '$scope',
    '$filter',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings',
    'JobStrings'
];

export default InstanceJobsController;