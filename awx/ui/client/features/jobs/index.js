import JobsStrings from './jobs.strings';
import jobsRoute from './routes/jobs.route';
import { jobsSchedulesRoute, jobsSchedulesEditRoute } from '../../src/scheduler/schedules.route';
import jobsListController from './jobsList.controller';

const MODULE_NAME = 'at.features.jobs';

angular
    .module(MODULE_NAME, [])
    .service('JobsStrings', JobsStrings)
    .controller('jobsListController', jobsListController)
    .run(['$stateExtender', ($stateExtender) => {
        $stateExtender.addState(jobsRoute);
        $stateExtender.addState(jobsSchedulesRoute);
        $stateExtender.addState(jobsSchedulesEditRoute);
    }]);

export default MODULE_NAME;
