import jobTemplates from './job-templates/main';
import jobs from './jobs/main';

export default
    angular.module('DashboardListsModules', [jobTemplates.name, jobs.name]);
