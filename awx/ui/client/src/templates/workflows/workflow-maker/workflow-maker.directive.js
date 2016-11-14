/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowMakerController from './workflow-maker.controller';

export default ['templateUrl', 'CreateDialog', 'Wait', '$state',
    function(templateUrl, CreateDialog, Wait, $state) {
        return {
            scope: {
                treeData: '=',
                canAddWorkflowJobTemplate: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('job-templates/workflow-maker/workflow-maker'),
            controller: workflowMakerController,
            link: function(scope) {
                CreateDialog({
                    id: 'workflow-modal-dialog',
                    scope: scope,
                    width: 1400,
                    height: 720,
                    draggable: false,
                    dialogClass: 'SurveyMaker-dialog',
                    position: ['center', 20],
                    onClose: function() {
                        $('#workflow-modal-dialog').empty();
                    },
                    onOpen: function() {
                        Wait('stop');

                        // Let the modal height be variable based on the content
                        // and set a uniform padding
                        $('#workflow-modal-dialog').css({ 'padding': '20px' });

                    },
                    _allowInteraction: function(e) {
                        return !!$(e.target).is('.select2-input') || this._super(e);
                    },
                    callback: 'WorkflowDialogReady'
                });
                if (scope.removeWorkflowDialogReady) {
                    scope.removeWorkflowDialogReady();
                }
                scope.removeWorkflowDialogReady = scope.$on('WorkflowDialogReady', function() {
                    $('#workflow-modal-dialog').dialog('open');

                    scope.$broadcast("refreshWorkflowChart");
                });

                scope.closeDialog = function() {
                    $('#workflow-modal-dialog').dialog('destroy');

                    $state.go('^');
                };
            }
        };
    }
];
