export default
    function CreateLaunchDialog($compile, CreateDialog, Wait, ParseTypeChange, i18n) {
        return function(params) {
            var buttons,
            scope = params.scope,
            html = params.html,
            // job_launch_data = {},
            callback = params.callback || 'PlaybookLaunchFinished',
            // url = params.url,
            e;

            // html+='<br>job_launch_form.$valid = {{job_launch_form.$valid}}<br>';
            html+='</form>';
            $('#password-modal').empty().html(html);
            $('#password-modal').find('#job_extra_vars').before(scope.helpContainer);
            e = angular.element(document.getElementById('password-modal'));
            $compile(e)(scope);

            if(scope.prompt_for_vars===true){
                ParseTypeChange({ scope: scope, field_id: 'job_extra_vars' , variable: "extra_vars"});
            }

            buttons = [{
                label: i18n._("Cancel"),
                onClick: function() {
                    $('#password-modal').dialog('close');
                    // scope.$emit('CancelJob');
                    // scope.$destroy();
                },
                "class": "btn btn-default",
                "id": "password-cancel-button"
            },{
                label: i18n._("Launch"),
                onClick: function() {
                    scope.$emit(callback);
                    $('#password-modal').dialog('close');
                },
                "class": "btn btn-primary",
                "id": "password-accept-button"
            }];

            CreateDialog({
                id: 'password-modal',
                scope: scope,
                buttons: buttons,
                width: 620,
                height: "auto",
                minWidth: 500,
                title: i18n._('Launch Configuration'),
                callback: 'DialogReady',
                onOpen: function(){
                    Wait('stop');
                }
            });

            if (scope.removeDialogReady) {
                scope.removeDialogReady();
            }
            scope.removeDialogReady = scope.$on('DialogReady', function() {
                $('#password-modal').dialog('open');
                $('#password-accept-button').attr('ng-disabled', 'job_launch_form.$invalid' );
                e = angular.element(document.getElementById('password-accept-button'));
                $compile(e)(scope);
            });
        };
    }

CreateLaunchDialog.$inject =
    [   '$compile',
        'CreateDialog',
        'Wait',
        'ParseTypeChange',
        'i18n'
    ];
