import generateList from './list-generator.factory';
import toolbarButton from './toolbar-button.directive';
import generatorHelpers from 'tower/shared/generator-helpers';
import multiSelectList from 'tower/shared/multi-select-list/main';

export default
    angular.module('listGenerator', [generatorHelpers.name, multiSelectList.name])
        .factory('generateList', generateList)
        .directive('toolbarButton', toolbarButton);
