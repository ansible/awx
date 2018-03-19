import atFeaturesUsersTokens from '~features/users/tokens';

const MODULE_NAME = 'at.features.users';

angular
    .module(MODULE_NAME, [atFeaturesUsersTokens]);

export default MODULE_NAME;
