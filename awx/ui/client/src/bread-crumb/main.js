import breadCrumb from './bread-crumb.directive';
import breadCrumbService from './bread-crumb.service';

export default
    angular.module('breadCrumb', [])
        .service('BreadCrumbService', breadCrumbService)
        .directive('breadCrumb', breadCrumb);
