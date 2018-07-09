import atLibServices from '~services';
import atLibComponents from '~components';
import atLibModels from '~models';

import atFeaturesApplications from '~features/applications';
import atFeaturesCredentials from '~features/credentials';
import atFeaturesOutput from '~features/output';
import atFeaturesTemplates from '~features/templates';
import atFeaturesUsers from '~features/users';
import atFeaturesJobs from '~features/jobs';
import atFeaturesPortalMode from '~features/portalMode';

const MODULE_NAME = 'at.features';

angular.module(MODULE_NAME, [
    atLibServices,
    atLibComponents,
    atLibModels,
    atFeaturesApplications,
    atFeaturesCredentials,
    atFeaturesTemplates,
    atFeaturesUsers,
    atFeaturesJobs,
    atFeaturesOutput,
    atFeaturesTemplates,
    atFeaturesPortalMode,
]);

export default MODULE_NAME;
