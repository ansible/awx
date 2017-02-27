import form from './question-definition.form';

export default
    angular.module('jobTemplates.surveyMaker.shared', [])
        .value('questionDefinitionForm', form);
