export default
    function InitiatePlaybookRun($location, GetBasePath, Empty, $compile) {

            // This factory drops the submit-job directive into the dom which
            // either launches the job (when no user input is needed) or shows
            // the user a job sumbission modal with varying steps based on what
            // is being prompted/what passwords are needed.

            return function (params) {
                var scope = params.scope.$new(),
                id = params.id,
                relaunch = params.relaunch || false,
                system_job = params.system_job || false;
                scope.job_template_id = id;

                var el = $compile( "<submit-job data-submit-job-id=" + id + " data-submit-job-system=" + system_job + " data-submit-job-relaunch=" + relaunch + "></submit-job>" )( scope );
                $('#content-container').remove('submit-job').append( el );
            };
        }

InitiatePlaybookRun.$inject =
    [   '$location',
        'GetBasePath',
        'Empty',
        '$compile'
    ];
