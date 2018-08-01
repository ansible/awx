import atLibServices from '~services';
import atLibComponents from '~components';
import atLibModels from '~models';

import atFeaturesApplications from '~features/applications';
import atFeaturesCredentials from '~features/credentials';
import atFeaturesInventoryScripts from '~features/inventory-scripts';
import atFeaturesJobs from '~features/jobs';
import atFeaturesOutput from '~features/output';
import atFeaturesTemplates from '~features/templates';
import atFeaturesUsers from '~features/users';

const MODULE_NAME = 'at.features';

angular.module(MODULE_NAME, [
    atLibServices,
    atLibComponents,
    atLibModels,
    atFeaturesApplications,
    atFeaturesCredentials,
    atFeaturesInventoryScripts,
    atFeaturesJobs,
    atFeaturesOutput,
    atFeaturesTemplates,
    atFeaturesUsers,
]);

export default MODULE_NAME;
