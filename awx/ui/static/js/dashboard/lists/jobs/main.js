import JobsListDirective from 'tower/dashboard/lists/jobs/jobs-list.directive';

export default angular.module('JobsList', [])
    .directive('jobsList', JobsListDirective);
