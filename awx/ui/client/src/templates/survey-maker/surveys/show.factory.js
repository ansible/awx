export default
    function ShowFactory(Wait, CreateDialog, Empty, $compile) {
        return function(params) {
            // Set modal dimensions based on viewport width

            var scope = params.scope,
                callback = params.callback,
                mode = (params.mode) ? params.mode : "survey-maker",
                title = params.title,
                element,
                target = (mode==='survey-taker') ? 'password-modal' : "survey-modal-dialog";

            CreateDialog({
                id: target,
                title: title,
                scope: scope,
                width: 1200,
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
        'Empty',
        '$compile'
    ];
