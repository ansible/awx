import getBrowserData from './browser-data.factory';
import ngApp from './ng-app.directive';

export default
    angular.module('browserData', [])
        .directive('ngApp', ngApp)
        .factory('browserData', getBrowserData);
