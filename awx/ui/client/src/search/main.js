import tagSearchDirective from './tagSearch.directive';
import tagSearchService from './tagSearch.service';
import getSearchHtml from './getSearchHtml.service';

export default
    angular.module('search', [])
        .directive('tagSearch', tagSearchDirective)
        .factory('tagSearchService', tagSearchService)
        .factory('getSearchHtml', getSearchHtml);
