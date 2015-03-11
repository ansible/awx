import generateList from './list-generator.factory';

export default
    angular.module('listGenerator', [])
        .factory('generateList', generateList);
