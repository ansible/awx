import jobTemplates from 'tower/dashboard/lists/job-templates/main';
import jobs from 'tower/dashboard/lists/jobs/main';

export default
    angular.module('DashboardListsModules', [jobTemplates.name, jobs.name]);
