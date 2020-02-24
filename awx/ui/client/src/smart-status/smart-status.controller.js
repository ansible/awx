/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$filter', 'i18n', 'JobsStrings',
    function ($scope, $filter, i18n, JobsStrings) {

        const strings = JobsStrings;

        function isFailureState(status) {
            return status === 'failed' || status === 'error' || status === 'canceled';
        }

        function getTranslatedStatusString(status) {
            switch (status) {
                case 'new':
                    return strings.get('list.NEW');
                case 'pending':
                    return strings.get('list.PENDING');
                case 'waiting':
                    return strings.get('list.WAITING');
                case 'running':
                    return strings.get('list.RUNNING');
                case 'successful':
                    return strings.get('list.SUCCESSFUL');
                case 'failed':
                    return strings.get('list.FAILED');
                case 'error':
                    return strings.get('list.ERROR');
                case 'canceled':
                    return strings.get('list.CANCELED');
                default:
                    return status;
            }
        }

        function init(){
            var singleJobStatus = true;
            var firstJobStatus;
            var recentJobs = $scope.jobs;
            var detailsBaseUrl;

            if(!recentJobs){
                return;
            }

            var sparkData =
            _.sortBy(recentJobs.map(function(job) {
                const finished = $filter('longDate')(job.finished) || job.status+"";

                // We now get the job type of recent jobs associated with a JT
                if (job.type === 'workflow_job') {
                    detailsBaseUrl = '/#/workflows/';
                } else if (job.type === 'job') {
                    detailsBaseUrl = '/#/jobs/playbook/';
                }

                const data = {
                    status: job.status,
                    jobId: job.id,
                    sortDate: job.finished || "running" + job.id,
                    finished: finished,
                    status_tip: `${i18n._('JOB ID')}: ${job.id} <br>${i18n._('STATUS')}: ${getTranslatedStatusString(job.status).toUpperCase()} <br>${i18n._('FINISHED')}: ${finished}`,
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
        $scope.$watch('jobs', function(){
            init();
        }, true);

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
