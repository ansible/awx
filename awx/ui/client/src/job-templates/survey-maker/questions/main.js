import questionScope from './question-scope.factory';
import edit from './edit.factory';

export default
    angular.module('jobTemplates.surveyMaker.questions', [])
        .factory('questionScope', questionScope)
        .factory('editQuestion', edit);
