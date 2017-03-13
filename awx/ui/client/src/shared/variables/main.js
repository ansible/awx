import ParseVariableString from './parse-variable-string.factory';
import SortVariables from './sort-variables.factory';
import ToJSON from './to-json.factory';

export default
    angular.module('variables', [])
        .factory('ParseVariableString', ParseVariableString)
        .factory('SortVariables', SortVariables)
        .factory('ToJSON', ToJSON);
