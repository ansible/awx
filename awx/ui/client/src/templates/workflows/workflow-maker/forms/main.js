import workflowLinkForm from './workflow-link-form.directive';
import workflowNodeForm from './workflow-node-form.directive';

export default
    angular.module('templates.workflowMaker.forms', [])
        .directive('workflowLinkForm', workflowLinkForm)
        .directive('workflowNodeForm', workflowNodeForm);
