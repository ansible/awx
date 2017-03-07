import prepend from './prepend.filter';
import append from './append.filter';
import isEmpty from './is-empty.filter';
import capitalize from './capitalize.filter';
import longDate from './long-date.filter';
import sanitize from './xss-sanitizer.filter';
import formatEpoch from './format-epoch.filter';

export default
    angular.module('stringFilters', [])
        .filter('prepend', prepend)
        .filter('append', append)
        .filter('isEmpty', isEmpty)
        .filter('capitalize', capitalize)
        .filter('longDate', longDate)
        .filter('sanitize', sanitize)
        .filter('formatEpoch', formatEpoch);
