import atLibServices from '~services';
import atLibComponents from '~components';
import atLibModels from '~models';

import atFeaturesCredentials from '~features/credentials';
import atFeaturesLayout from '~features/layout';

const MODULE_NAME = 'at.features';

angular.module(MODULE_NAME, [
    atLibServices,
    atLibComponents,
    atLibModels,
    atFeaturesCredentials,
    atFeaturesLayout
]);

export default MODULE_NAME;
