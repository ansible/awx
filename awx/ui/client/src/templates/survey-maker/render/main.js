import surveyQuestion from './survey-question.directive';
import multipleChoice from './multiple-choice.directive';
import multiSelect from './multiselect.directive';

export default
    angular.module('jobTemplates.surveyMaker.render', [])
        .directive('surveyQuestion', surveyQuestion)
        .directive('multipleChoice', multipleChoice)
        .directive('multiSelect', multiSelect);
