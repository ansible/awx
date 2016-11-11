import helper from './workflow-help.service';
import workflowMaker from './workflow-maker.directive';
import WorkflowMakerController from './workflow-maker.controller';

export default
    angular.module('jobTemplates.workflowMaker', [])
        .service('WorkflowHelpService', helper)
        // In order to test this controller I had to expose it at the module level
        // like so.  Is this correct?  Is there a better pattern for doing this?
        .controller('WorkflowMakerController', WorkflowMakerController)
        .directive('workflowMaker', workflowMaker);
