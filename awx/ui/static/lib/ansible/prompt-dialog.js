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

'use strict';

angular.module('PromptDialog', ['Utilities'])
    .factory('Prompt', ['$rootScope', '$compile', 'Alert', function($rootScope, $compile, Alert) {
    return function(params) {
        
        var dialog = angular.element(document.getElementById('prompt-modal'));
        var scope = dialog.scope();
        
        scope.promptHeader = params.hdr;
        scope.promptBody = params.body;
        scope.promptAction = params.action;
        
        var cls = (params['class'] == null || params['class'] == undefined) ? 'btn-danger' : params['class'];
        
        $('#prompt_action_btn').removeClass(cls).addClass(cls); 
        
        $(dialog).modal({
            backdrop: 'static',
            keyboard: true,
            show: true
            });
        }
    }]);
    