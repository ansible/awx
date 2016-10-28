import directive from './column-sort.directive';
import controller from './column-sort.controller';

export default
	angular.module('ColumnSortModule', [])
		.directive('columnSort', directive)
		.controller('ColumnSortController', controller);
