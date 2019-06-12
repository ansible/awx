/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowMakerController from './workflow-maker.controller';

export default ['templateUrl', 'CreateDialog', 'Wait', '$state', '$window',
    function(templateUrl, CreateDialog, Wait, $state, $window) {
        return {
            scope: {
                workflowJobTemplateObj: '=',
                canAddOrEdit: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('templates/workflows/workflow-maker/workflow-maker'),
            controller: workflowMakerController,
            link: function(scope) {

                let availableHeight = $(window).height(),
                    availableWidth = $(window).width(),
                    minimumWidth = 682,
                    minimumHeight = 400;

                CreateDialog({
                    id: 'workflow-modal-dialog',
                    scope: scope,
                    width: availableWidth > minimumWidth ? availableWidth : minimumWidth,
                    height: availableHeight > minimumHeight ? availableHeight : minimumHeight,
                    draggable: false,
                    dialogClass: 'WorkflowMaker-dialog',
                    position: ['center', 20],
                    onClose: function() {
                        $('#workflow-modal-dialog').empty();
                        $('body').removeClass('WorkflowMaker-preventBodyScrolling');
                    },
                    onOpen: function() {
                        Wait('stop');
                        $('body').addClass('WorkflowMaker-preventBodyScrolling');

                        // Let the modal height be variable based on the content
                        // and set a uniform padding
                        $('#workflow-modal-dialog').css({ 'padding': '20px' });
                        $('#workflow-modal-dialog').outerHeight(availableHeight > minimumHeight ? availableHeight : minimumHeight);
                        $('#workflow-modal-dialog').outerWidth(availableWidth > minimumWidth ? availableWidth : minimumWidth);

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

                    scope.modalOpen = true;

                    scope.$broadcast("refreshWorkflowChart");
                });

                scope.closeDialog = function(exitWithUnsavedChanges) {
                    if (
                        !scope.canAddOrEdit ||
                        exitWithUnsavedChanges ||
                        !(scope.workflowChangesUnsaved || scope.workflowChangesStarted)
                    ) {
                        scope.unsavedChangesVisible = false;
                        $('#workflow-modal-dialog').dialog('destroy');
                        $('body').removeClass('WorkflowMaker-preventBodyScrolling');

                        $state.go('^');
                    } else {
                        scope.unsavedChangesVisible = true;
                    }
                };

                function onResize(){
                    availableHeight = $(window).height();
                    availableWidth = $(window).width();
                    $('#workflow-modal-dialog').outerHeight(availableHeight > minimumHeight ? availableHeight : minimumHeight);
                    $('#workflow-modal-dialog').outerWidth(availableWidth > minimumWidth ? availableWidth : minimumWidth);

                    scope.$broadcast('workflowMakerModalResized');
                }

                function cleanUpResize() {
                    angular.element($window).off('resize', onResize);
                }

                angular.element($window).on('resize', onResize);
                scope.$on('$destroy', cleanUpResize);
            }
        };
    }
];
