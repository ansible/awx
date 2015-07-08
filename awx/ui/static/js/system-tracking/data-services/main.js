import factScanDataService from './fact-scan-data.service';
import getDataForComparison from './get-data-for-comparison.factory';
import getModuleOptions from './get-module-options.factory';
import resolveEmptyVersions from './resolve-empty-versions.factory';
import shared from 'tower/shared/main';

export default
    angular.module('systemTracking.dataServices', [shared.name])
        .factory('getModuleOptions', getModuleOptions)
        .factory('getDataForComparison', getDataForComparison)
        .factory('resolveEmptyVersions', resolveEmptyVersions)
        .service('factScanDataService', factScanDataService);
