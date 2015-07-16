import JobsListDirective from './jobs-list.directive';

export default angular.module('JobsList', [])
    .directive('jobsList', JobsListDirective);
