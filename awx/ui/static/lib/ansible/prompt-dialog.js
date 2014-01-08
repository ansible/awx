/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * PromptDialog
 * Prompt the user with a Yes/No dialog to confirm an action such 
 * as Delete.  Assumes a hidden dialog already exists in $scope.
 * See example at bottom. If user responds with Yes, execute action 
 * parameter.
 *
 * params: { hdr: 'header msg', 
 *           body: 'body text/html',
 *           class: 'btn-class for Yes button',  --defaults to btn-danger
 *           action: function() {}  --action to take, if use clicks Yes
 *           }
 */

angular.module('PromptDialog', ['Utilities'])
    .factory('Prompt', ['Alert', function(Alert) {
    return function(params) {
        
        var dialog = angular.element(document.getElementById('prompt-modal'));
        var scope = dialog.scope(); 
        
        scope.promptHeader = params.hdr;
        scope.promptBody = params.body;
        scope.promptAction = params.action;
        var cls = (params['class'] == null || params['class'] == undefined) ? 'btn-danger' : params['class'];
        
        $('#prompt_action_btn').addClass(cls); // Use jquery because django template engine conflicts with Angular's
                                               // use of {{...}}
        
        $(dialog).modal({
            backdrop: 'static',
            keyboard: true,
            show: true
            });
        }
    }]);
    