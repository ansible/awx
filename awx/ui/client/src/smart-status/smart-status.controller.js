/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$filter',
    function ($scope, $filter) {

        function isFailureState(status) {
            return status === 'failed' || status === 'error' || status === 'canceled';
        }

        function init(){
            var singleJobStatus = true;
            var firstJobStatus;
            var recentJobs = $scope.jobs;
            var detailsBaseUrl;

            if(!recentJobs){
                return;
            }

            // unless we explicitly define a value for the template-type attribute when invoking the
            // directive, assume the status icons are for a regular (non-workflow) job when building
            // the details url path
            if (typeof $scope.templateType !== 'undefined' && $scope.templateType === 'workflow_job_template') {
                detailsBaseUrl = '/#/workflows/';
            } else {
                detailsBaseUrl = '/#/jobs/playbook/';
            }

            var sparkData =
            _.sortBy(recentJobs.map(function(job) {

                const finished = $filter('longDate')(job.finished) || job.status+"";

                const data = {
                    status: job.status,
                    jobId: job.id,
                    sortDate: job.finished || "running" + job.id,
                    finished: finished,
                    status_tip: "JOB ID: " + job.id + "<br>STATUS: " + job.status.toUpperCase() + "<br>FINISHED: " + finished,
                    detailsUrl: detailsBaseUrl + job.id
                };

                // If we've already determined that there are both failed and successful jobs OR if the current job in the loop is
                // pending/waiting/running then we don't worry about checking for a single job status
                if(singleJobStatus && (isFailureState(job.status) || job.status === "successful")) {
                    if(firstJobStatus) {
                        // We've already been through at least once and have a first job status
                        if(!(isFailureState(firstJobStatus) && isFailureState(job.status) || firstJobStatus === job.status)) {
                            // We have a different status in the array
                            singleJobStatus = false;
                        }
                    }
                    else {
                        // We haven't set a first job status yet so go ahead set it
                        firstJobStatus = job.status;
                    }
                }

                return data;
            }), "sortDate").reverse();

            $scope.singleJobStatus = singleJobStatus;

            $scope.sparkArray = sparkData;
            $scope.placeholders = new Array(10 - sparkData.length);
        }
        $scope.$watchCollection('jobs', function(){
            init();
        });

}];

//
//
// JOB_STATUS_CHOICES = [
//         ('new', _('New')),                  # Job has been created, but not started.
//         ('pending', _('Pending')),          # Job has been queued, but is not yet running.
//         ('waiting', _('Waiting')),          # Job is waiting on an update/dependency.
//         ('running', _('Running')),          # Job is currently running.
//         ('successful', _('Successful')),    # Job completed successfully.
//         ('failed', _('Failed')),            # Job completed, but with failures.
//         ('error', _('Error')),              # The job was unable to run.
//         ('canceled', _('Canceled')),        # The job was canceled before completion.
// final states only*****
//     ]
//
