/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
  /**
 *  @ngdoc function
 *  @name lib.ansible.function:prompt-dialog
 *  @description
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
/**
* @ngdoc method
* @name lib.ansible.function:prompt-dialog#PromptDialog
* @methodOf lib.ansible.function:prompt-dialog
* @description discuss difference b/t this and other modals
*/
angular.module('PromptDialog', ['Utilities'])
    .factory('Prompt', ['$sce',
        function ($sce) {
            return function (params) {

                var dialog = angular.element(document.getElementById('prompt-modal')),
                    scope = dialog.scope(), cls, local_backdrop;

                scope.promptHeader = params.hdr;
                scope.promptBody = $sce.trustAsHtml(params.body);
                scope.promptAction = params.action;

                local_backdrop = (params.backdrop === undefined) ? "static" : params.backdrop;

                cls = (params['class'] === null || params['class'] === undefined) ? 'btn-danger' : params['class'];

                $('#prompt_action_btn').removeClass(cls).addClass(cls);

                $('#prompt-modal').off('hidden.bs.modal');
                $('#prompt-modal').modal({
                    backdrop: local_backdrop,
                    keyboard: true,
                    show: true
                });
            };
        }
    ]);