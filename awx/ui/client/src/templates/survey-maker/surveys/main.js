import add from './add.factory';
import edit from './edit.factory';
import _delete from './delete.factory';
import init from './init.factory';
import show from './show.factory';

export default
    angular.module('jobTemplates.surveyMaker.surveys', [])
        .factory('showSurvey', show)
        .factory('addSurvey', add)
        .factory('editSurvey', edit)
        .factory('deleteSurvey', _delete)
        .factory('initSurvey', init);
