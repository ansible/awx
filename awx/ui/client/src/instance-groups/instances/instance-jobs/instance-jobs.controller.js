
function InstanceJobsController ($scope, $filter, $state, model, strings, jobStrings, Instance) {
    const vm = this || {};
    let { instance } = model;
    const instance_id = instance.get('id');

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

    $scope.$on('ws-jobs', () => {
        new Instance(['get', 'options'], [instance_id, instance_id])
            .then((data) =>  {
                return data.extend('get', 'jobs', {params: {page_size: "10", order_by: "-finished"}});
            })
            .then((data) => {
                instance = data;
                init();
            });
    });

}

InstanceJobsController.$inject = [
    '$scope',
    '$filter',
    '$state',
    'resolvedModels',
    'InstanceGroupsStrings',
    'JobStrings',
    'InstanceModel'
];

export default InstanceJobsController;
