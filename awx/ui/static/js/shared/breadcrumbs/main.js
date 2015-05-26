import breadcrumbs from './breadcrumbs.directive';
import breadcrumb from './breadcrumb.directive';

export default
    angular.module('breadcrumbs', [])
        .directive('breadcrumb', breadcrumb)
        .directive('breadcrumbs', breadcrumbs);
