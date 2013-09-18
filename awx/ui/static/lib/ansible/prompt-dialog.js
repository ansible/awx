/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
        //  

        var dialog = angular.element(document.getElementById('prompt-modal'));
        var scope = dialog.scope(); 
        scope.promptHeader = params.hdr;
        scope.promptBody = params.body;
        var cls = (params['class'] == null || params['class'] == undefined) ? 'btn-danger' : params['class'];
        $('#prompt_action_btn').addClass(cls); //Use jquery because django template engine conflicts with Angular's
                                               // use of {{...}}
        //scope.id = params.id; 
        //scope.url = params.url; 
        scope.promptAction = params.action;
        $(dialog).modal({
            backdrop: 'static',
            keyboard: true,
            show: true
            });
        }
    }]);
    



<!-- Generic Modal dialog. Use to confirming an action (i.e. Delete) -->
//    <div id="prompt-modal" class="modal hide">
//      <div class="modal-header">
//        <button type="button" class="close" data-target="#prompt-modal" 
//                        data-dismiss="modal" aria-hidden="true">&times;</button>
//        <h3 ng-bind="promptHeader"></h3>
//      </div>
//      <div class="modal-body" ng-bind="promptBody">
//      </div>
//      <div class="modal-footer">
//        <a href="#" data-target="#prompt-modal" data-dismiss="modal" class="btn">No</a>
//        <a href="" ng-click="promptAction()" class="btn {{ promptBtnClass }}">Yes</a>
//      </div>
//    </div>