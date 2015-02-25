import conversionService from './conversions.service'
import smartStatusGraph from './smart-status.directive'
import controller from './smart-status.controller'

export default
    angular.module('systemStatus', [])
        .service('conversions', conversionService)
        .directive('smartStatusGraph', smartStatusGraph)
        .controller('smartStatusLoad', controller);
