import finalize from './finalize.factory';
import edit from './edit.factory';

export default
    angular.module('jobTemplates.surveyMaker.questions', [])
        .factory('finalizeQuestion', finalize)
        .factory('editQuestion', edit);
