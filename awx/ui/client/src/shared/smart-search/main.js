import directive from './smart-search.directive';
import controller from './smart-search.controller';
import service from './queryset.service';
import DjangoSearchModel from './django-search-model.class';


export default
angular.module('SmartSearchModule', [])
    .directive('smartSearch', directive)
    .controller('SmartSearchController', controller)
    .service('QuerySet', service)
    .constant('DjangoSearchModel', DjangoSearchModel);
