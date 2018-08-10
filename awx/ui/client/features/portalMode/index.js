import PortalModeStrings from './portalMode.strings';

import templatesRoute from './routes/portalModeTemplatesList.route';
import myJobsRoute from './routes/portalModeMyJobs.route';
import allJobsRoute from './routes/portalModeAllJobs.route';

const MODULE_NAME = 'at.features.portalMode';

angular
    .module(MODULE_NAME, [])
    .service('PortalModeStrings', PortalModeStrings)
    .run(['$stateExtender', ($stateExtender) => {
        $stateExtender.addState(templatesRoute);
        $stateExtender.addState(myJobsRoute);
        $stateExtender.addState(allJobsRoute);
    }]);

export default MODULE_NAME;
