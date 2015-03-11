import generateList from './list-generator.factory';
import toolbarButton from './toolbar-button.directive';
import generatorHelpers from 'tower/shared/generator-helpers';

export default
    angular.module('listGenerator', [generatorHelpers.name])
        .factory('generateList', generateList)
        .directive('toolbarButton', toolbarButton);
