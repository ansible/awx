import layout from '~features/layout/layout.directive';

const MODULE_NAME = 'at.features.credentials';

angular
    .module(MODULE_NAME, [])
    .directive('atLayout', layout);
