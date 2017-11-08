import atLibServices from '~services';
import atLibComponents from '~components';
import atLibModels from '~models';

import atFeaturesCredentials from '~features/credentials';
import atFeaturesNetworking from '~features/networking';

const MODULE_NAME = 'at.features';

angular.module(MODULE_NAME, [
    atLibServices,
    atLibComponents,
    atLibModels,
    atFeaturesCredentials,
    atFeaturesNetworking
]);

export default MODULE_NAME;
