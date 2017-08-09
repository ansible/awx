export default
    function ShowFactory(Wait, CreateDialog, $compile) {
        return function(params) {
            // Set modal dimensions based on viewport width

            let scope = params.scope,
                callback = params.callback,
                mode = (params.mode) ? params.mode : "survey-maker",
                title = params.title,
                element,
                target = (mode==='survey-taker') ? 'password-modal' : "survey-modal-dialog",
                width = params.scope.can_edit ? 'calc(100vw - 50px)' : 600;


            CreateDialog({
                id: target,
                title: title,
                scope: scope,
                width: width,
                minWidth: 400,
                draggable: false,
                dialogClass: 'SurveyMaker-dialog',
                onClose: function() {
                    $('#'+target).empty();
                },
                onOpen: function() {
                    Wait('stop');

                    // Let the modal height be variable based on the content
                    // and set a uniform padding
                    $('#'+target).css({'height': 'auto', 'padding': '20px'});

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
        '$compile'
    ];
