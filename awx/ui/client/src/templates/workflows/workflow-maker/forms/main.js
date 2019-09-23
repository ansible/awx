import workflowLinkForm from './workflow-link-form.directive';
import workflowNodeForm from './workflow-node-form.directive';
import workflowNodeFormService from './workflow-node-form.service';

export default
    angular.module('templates.workflowMaker.forms', [])
        .directive('workflowLinkForm', workflowLinkForm)
        .directive('workflowNodeForm', workflowNodeForm)
        .service('WorkflowNodeFormService', workflowNodeFormService);
