import prepend from './prepend.filter';
import append from './append.filter';

export default
    angular.module('stringFilters', [])
        .filter('prepend', prepend)
        .filter('append', append);
