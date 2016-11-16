import workflowMaker from './workflow-maker.directive';
import WorkflowMakerController from './workflow-maker.controller';

export default
    angular.module('templates.workflowMaker', [])
        // In order to test this controller I had to expose it at the module level
        // like so.  Is this correct?  Is there a better pattern for doing this?
        .controller('WorkflowMakerController', WorkflowMakerController)
        .directive('workflowMaker', workflowMaker);
