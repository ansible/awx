import directive from './smart-search.directive';
import controller from './smart-search.controller';
import service from './queryset.service';
import DjangoSearchModel from './django-search-model.class';
import smartSearchService from './smart-search.service';

export default
angular.module('SmartSearchModule', [])
    .directive('smartSearch', directive)
    .controller('SmartSearchController', controller)
    .service('QuerySet', service)
    .service('SmartSearchService', smartSearchService)
    .constant('DjangoSearchModel', DjangoSearchModel);
