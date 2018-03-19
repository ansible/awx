import TokensStrings from './tokens.strings';

const MODULE_NAME = 'at.features.users.tokens';

angular
    .module(MODULE_NAME, [])
    .service('TokensStrings', TokensStrings);

export default MODULE_NAME;
