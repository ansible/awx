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
            var sparkData =
            _.sortBy(recentJobs.map(function(job) {

                var data = {};

                if (job.status === 'successful') {
                    data.value = 1;
                    data.smartStatus = "<i class=\"fa DashboardList-status SmartStatus-tooltip--success icon-job-successful\"></i>  " + job.status.toUpperCase();
                } else if (isFailureState(job.status)) {
                    data.value = -1;
                    data.smartStatus = "<i class=\"fa DashboardList-status SmartStatus-tooltip--failed icon-job-successful\"></i>  " + job.status.toUpperCase();
                } else {
                    data.value = 0;
                    data.smartStatus = "<i class=\"fa DashboardList-status SmartStatus-tooltip--running icon-job-successful\"></i>  " + job.status.toUpperCase();
                }

                data.jobId = job.id;
                data.sortDate = job.finished || "running" + data.jobId;
                data.finished = $filter('longDate')(job.finished) || job.status+"";
                data.status_tip = "JOB ID: " + data.jobId + "<br>STATUS: " + data.smartStatus + "<br>FINISHED: " + data.finished;

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
