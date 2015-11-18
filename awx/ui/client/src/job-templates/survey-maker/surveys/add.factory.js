export default
    function AddFactory($location, $routeParams, ShowSurveyModal, Wait) {
        return function(params) {
            var scope = params.scope;

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#survey-modal-dialog').dialog('open');
                scope.addQuestion();
            });
            Wait('start');
            $('#form-container').empty();
            scope.resetForm();
            ShowSurveyModal({ title: "Add Survey", scope: scope, callback: 'DialogReady' });
        };
    }

AddFactory.$inject =
    [   '$location',
        '$routeParams',
        'showSurvey',
        'Wait'
    ];
