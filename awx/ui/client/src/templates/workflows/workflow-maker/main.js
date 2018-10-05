import workflowMaker from './workflow-maker.directive';
import WorkflowMakerController from './workflow-maker.controller';
import workflowMakerForms from './forms/main';

export default
    angular.module('templates.workflowMaker', [workflowMakerForms.name])
        // In order to test this controller I had to expose it at the module level
        // like so.  Is this correct?  Is there a better pattern for doing this?
        .controller('WorkflowMakerController', WorkflowMakerController)
        .directive('workflowMaker', workflowMaker);
