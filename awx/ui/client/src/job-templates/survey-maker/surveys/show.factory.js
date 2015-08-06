export default
    function ShowFactory(Wait, CreateDialog, Empty, $compile) {
        return function(params) {
            // Set modal dimensions based on viewport width

            var scope = params.scope,
                callback = params.callback,
                mode = (params.mode) ? params.mode : "survey-maker",
                title = params.title,
                element,
                target = (mode==='survey-taker') ? 'password-modal' : "survey-modal-dialog",
                buttons = [{
                "label": "Cancel",
                "onClick": function() {
                    scope.cancelSurvey(this);
                },
                "icon": "fa-times",
                "class": "btn btn-default",
                "id": "survey-close-button"
            },{
                "label": (mode==='survey-taker') ? "Launch" : "Save" ,
                "onClick": function() {
                    setTimeout(function(){
                        scope.$apply(function(){
                            if(mode==='survey-taker'){
                                scope.$emit('SurveyTakerCompleted');
                            } else{
                                scope.saveSurvey();
                            }
                        });
                    });
                },
                "icon":  (mode==='survey-taker') ? "fa-rocket" : "fa-check",
                "class": "btn btn-primary",
                "id": "survey-save-button"
            }];

            CreateDialog({
                id: target,
                title: title,
                scope: scope,
                buttons: buttons,
                width: 700,
                height: 725,
                minWidth: 400,
                onClose: function() {
                    $('#'+target).empty();
                },
                onOpen: function() {
                    Wait('stop');
                    if(mode!=="survey-taker"){
                        // if(scope.mode === 'add'){
                        //     $('#survey-save-button').attr('disabled' , true);
                        // } else
                        if(scope.can_edit === false){
                            $('#survey-save-button').attr('disabled', "disabled");
                        }
                        else {
                            $('#survey-save-button').attr('ng-disabled', "survey_questions.length<1 ");
                        }
                        element = angular.element(document.getElementById('survey-save-button'));
                        $compile(element)(scope);

                    }
                    if(mode==="survey-taker"){
                        $('#survey-save-button').attr('ng-disabled',  "survey_taker_form.$invalid");
                        element = angular.element(document.getElementById('survey-save-button'));
                        $compile(element)(scope);

                    }

                },
                _allowInteraction: function(e) {
                    return !!$(e.target).is('.select2-input') || this._super(e);
                },
                callback: callback
            });
        };
    }

ShowFactory.$inject =
    [   'Wait',
        'CreateDialog',
        'Empty',
        '$compile'
    ];

