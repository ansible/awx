export default
    function AddFactory(ShowSurveyModal, Wait) {
        return function(params) {
            var scope = params.scope;

            // This variable controls the survey on/off toggle beside the create survey
            // modal title.  We want this toggle to be on by default
            scope.survey_enabled = true;

            scope.isEditSurvey = false;

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#survey-modal-dialog').dialog('open');
                scope.generateAddQuestionForm();
            });
            Wait('start');
            ShowSurveyModal({ scope: scope, callback: 'DialogReady' });
        };
    }

AddFactory.$inject =
    [   'showSurvey',
        'Wait'
    ];
