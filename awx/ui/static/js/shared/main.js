import listGenerator from './list-generator/main';
import title from './title.directive';

export default
    angular.module('shared', [listGenerator.name])
        .directive('title', title);
