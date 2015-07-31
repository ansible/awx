export default
        function Init($location, DeleteSurvey, EditSurvey, AddSurvey, GenerateForm, SurveyQuestionForm, Wait, Alert,
            GetBasePath, Rest, ProcessErrors, $compile, FinalizeQuestion, EditQuestion, $sce) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                i, url, html, element,
                questions = [],
                form = SurveyQuestionForm,
                sce = params.sce;
            scope.sce = sce;
            scope.survey_questions = [];
            scope.answer_types=[
                {name: 'Text' , type: 'text'},
                {name: 'Textarea', type: 'textarea'},
                {name: 'Password', type: 'password'},
                {name: 'Multiple Choice (single select)', type: 'multiplechoice'},
                {name: 'Multiple Choice (multiple select)', type: 'multiselect'},
                {name: 'Integer', type: 'integer'},
                {name: 'Float', type: 'float'}
            ];

            scope.serialize = function(expression){
                return $sce.getTrustedHtml(expression);
            };

            scope.deleteSurvey = function() {
                DeleteSurvey({
                    scope: scope,
                    id: id,
                    // callback: 'SchedulesRefresh'
                });
            };

            scope.editSurvey = function() {
                if(scope.mode==='add'){
                    for(i=0; i<scope.survey_questions.length; i++){
                        questions.push(scope.survey_questions[i]);
                    }
                }
                EditSurvey({
                    scope: scope,
                    id: id,
                    // callback: 'SchedulesRefresh'
                });
            };

            scope.addSurvey = function() {
                AddSurvey({
                    scope: scope
                });
            };

            scope.cancelSurvey = function(me){
                if(scope.mode === 'add'){
                    questions = [];
                }
                else {
                    scope.survey_questions = [];
                }
                $(me).dialog('close');
            };

            scope.addQuestion = function(){
                var tmpMode = scope.mode;
                GenerateForm.inject(form, { id:'new_question', mode: 'add' , scope: scope, related: false, breadCrumbs: false});
                scope.mode = tmpMode;
                scope.required = true; //set the required checkbox to true via the ngmodel attached to scope.required.
                scope.text_min = null;
                scope.text_max = null;
                scope.int_min = null;
                scope.int_max = null;
                scope.float_min = null;
                scope.float_max = null;
                scope.duplicate = false;
                scope.invalidChoice = false;
                scope.minTextError = false;
                scope.maxTextError = false;
            };

            scope.addNewQuestion = function(){
                // $('#add_question_btn').on("click" , function(){
                scope.addQuestion();
                $('#survey_question_question_name').focus();
                $('#add_question_btn').attr('disabled', 'disabled');
                $('#add_question_btn').hide();
                $('#survey-save-button').attr('disabled' , 'disabled');
            // });
            };
            scope.editQuestion = function(index){
                scope.duplicate = false;
                EditQuestion({
                    index: index,
                    scope: scope,
                    question: (scope.mode==='add') ? questions[index] : scope.survey_questions[index]
                });
            };

            scope.deleteQuestion = function(index){
                element = $('.question_final:eq('+index+')');
                element.remove();
                if(scope.mode === 'add'){
                    questions.splice(index, 1);
                    scope.reorder();
                    if(questions.length<1){
                        $('#survey-save-button').attr('disabled', 'disabled');
                    }
                }
                else {
                    scope.survey_questions.splice(index, 1);
                    scope.reorder();
                    if(scope.survey_questions.length<1){
                        $('#survey-save-button').attr('disabled', 'disabled');
                    }
                }
            };

            scope.cancelQuestion = function(event){
                var elementID, key;
                if(event.target.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.id==="new_question"){
                    $('#new_question .aw-form-well').remove();
                    $('#add_question_btn').show();
                    $('#add_question_btn').removeAttr('disabled');
                    if(scope.mode === 'add' && questions.length>0){
                        $('#survey-save-button').removeAttr('disabled');
                    }
                    if(scope.mode === 'edit' && scope.survey_questions.length>0 && scope.can_edit===true){
                        $('#survey-save-button').removeAttr('disabled');
                    }

                } else {
                    elementID = event.target.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.id;
                    key = elementID.split('_')[1];
                    $('#'+elementID).empty();
                    if(scope.mode === 'add'){
                        if(questions.length>0){
                            $('#survey-save-button').removeAttr('disabled');
                        }
                        scope.finalizeQuestion(questions[key], key);
                    }
                    else if(scope.mode=== 'edit' ){
                        if(scope.survey_questions.length>0 && scope.can_edit === true){
                            $('#survey-save-button').removeAttr('disabled');
                        }
                        scope.finalizeQuestion(scope.survey_questions[key] , key);
                    }
                }
            };

            scope.questionUp = function(index){
                var animating = false,
                    clickedDiv = $('#question_'+index),
                    prevDiv = clickedDiv.prev(),
                    distance = clickedDiv.outerHeight();

                if (animating) {
                    return;
                }

                if (prevDiv.length) {
                    animating = true;
                    $.when(clickedDiv.animate({
                        top: -distance
                    }, 600),
                    prevDiv.animate({
                        top: distance
                    }, 600)).done(function () {
                        prevDiv.css('top', '0px');
                        clickedDiv.css('top', '0px');
                        clickedDiv.insertBefore(prevDiv);
                        animating = false;
                        if ( scope.mode === 'add'){
                            i = questions[index];
                            questions[index] = questions[index-1];
                            questions[index-1] = i;
                        } else {
                            i = scope.survey_questions[index];
                            scope.survey_questions[index] = scope.survey_questions[index-1];
                            scope.survey_questions[index-1] = i;
                        }
                        scope.reorder();
                    });
                }
            };

            scope.questionDown = function(index){
                var clickedDiv = $('#question_'+index),
                    nextDiv = clickedDiv.next(),
                    distance = clickedDiv.outerHeight(),
                    animating = false;

                if (animating) {
                    return;
                }

                if (nextDiv.length) {
                    animating = true;
                    $.when(clickedDiv.animate({
                        top: distance
                    }, 600),
                    nextDiv.animate({
                        top: -distance
                    }, 600)).done(function () {
                        nextDiv.css('top', '0px');
                        clickedDiv.css('top', '0px');
                        nextDiv.insertBefore(clickedDiv);
                        animating = false;
                        if(scope.mode === 'add'){
                            i = questions[index];
                            questions[index] = questions[Number(index)+1];
                            questions[Number(index)+1] = i;
                        } else {
                            i = scope.survey_questions[index];
                            scope.survey_questions[index] = scope.survey_questions[Number(index)+1];
                            scope.survey_questions[Number(index)+1] = i;
                        }
                        scope.reorder();
                    });
                }
            };

            scope.reorder = function(){
                if(scope.mode==='add'){
                    for(i=0; i<questions.length; i++){
                        questions[i].index=i;
                        $('.question_final:eq('+i+')').attr('id', 'question_'+i);
                    }
                }
                else {
                    for(i=0; i<scope.survey_questions.length; i++){
                        scope.survey_questions[i].index=i;
                        $('.question_final:eq('+i+')').attr('id', 'question_'+i);
                    }
                }
            };

            scope.finalizeQuestion= function(data, index){
                FinalizeQuestion({
                    scope: scope,
                    question: data,
                    id: id,
                    index: index
                });
            };

            scope.typeChange = function() {
                scope.minTextError = false;
                scope.maxTextError = false;
                scope.default = "";
                scope.default_multiselect = "";
                scope.default_float = "";
                scope.default_int = "";
                scope.default_textarea = "";
                scope.default_password = "" ;
                scope.choices = "";
                scope.text_min = "";
                scope.text_max = "" ;
                scope.textarea_min = "";
                scope.textarea_max = "" ;
                scope.password_min = "" ;
                scope.password_max = "" ;
                scope.int_min = "";
                scope.int_max = "";
                scope.float_min = "";
                scope.float_max = "";
                scope.survey_question_form.default.$setPristine();
                scope.survey_question_form.default_multiselect.$setPristine();
                scope.survey_question_form.default_float.$setPristine();
                scope.survey_question_form.default_int.$setPristine();
                scope.survey_question_form.default_textarea.$setPristine();
                scope.survey_question_form.default_password.$setPristine();
                scope.survey_question_form.choices.$setPristine();
                scope.survey_question_form.int_min.$setPristine();
                scope.survey_question_form.int_max.$setPristine();
            };

            scope.submitQuestion = function(event){
                var data = {},
                fld, i,
                choiceArray,
                answerArray,
                key, elementID;
                scope.invalidChoice = false;
                scope.duplicate = false;
                scope.minTextError = false;
                scope.maxTextError = false;

                if(scope.type.type==="text"){
                    if(scope.default.trim() !== ""){
                        if(scope.default.trim().length < scope.text_min && scope.text_min !== "" ){
                            scope.minTextError = true;
                        }
                        if(scope.text_max <  scope.default.trim().length && scope.text_max !== "" ){
                            scope.maxTextError = true;
                        }
                    }
                }

                if(scope.type.type==="textarea"){
                    if(scope.default_textarea.trim() !== ""){
                        if(scope.default_textarea.trim().length < scope.textarea_min && scope.textarea_min !== "" ){
                            scope.minTextError = true;
                        }
                        if(scope.textarea_max <  scope.default_textarea.trim().length && scope.textarea_max !== "" ){
                            scope.maxTextError = true;
                        }
                    }
                }

                if(scope.type.type==="password"){
                    if(scope.default_password.trim() !== ""){
                        if(scope.default_password.trim().length < scope.password_min && scope.password_min !== "" ){
                            scope.minTextError = true;
                        }
                        if(scope.password_max <  scope.default_password.trim().length && scope.password_max !== "" ){
                            scope.maxTextError = true;
                        }
                    }
                }

                if(scope.type.type==="multiselect" && scope.default_multiselect.trim() !== ""){
                    choiceArray = scope.choices.split(/\n/);
                    answerArray = scope.default_multiselect.split(/\n/);

                    if(answerArray.length>0){
                        for(i=0; i<answerArray.length; i++){
                            if($.inArray(answerArray[i], choiceArray)===-1){
                                scope.invalidChoice = true;
                            }
                        }
                    }
                }

                if(scope.type.type==="multiplechoice" && scope.default.trim() !== ""){
                    choiceArray = scope.choices.split(/\n/);
                    if($.inArray(scope.default, choiceArray)===-1){
                        scope.invalidChoice = true;
                    }
                }

                // validate that there aren't any questions using this var name.
                if(GenerateForm.mode === 'add'){
                    if(scope.mode === 'add'){
                        for(fld in questions){
                            if(questions[fld].variable === scope.variable){
                                scope.duplicate = true;
                            }
                        }
                    }
                    else if (scope.mode === 'edit'){
                        for(fld in scope.survey_questions){
                            if(scope.survey_questions[fld].variable === scope.variable){
                                scope.duplicate = true;
                            }
                        }
                    }
                }
                if(GenerateForm.mode === 'edit'){
                    elementID = event.target.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.id;
                    key = elementID.split('_')[1];
                    if(scope.mode==='add'){
                        for(fld in questions){
                            if(questions[fld].variable === scope.variable && fld!==key){
                                scope.duplicate = true;
                            }
                        }
                    }
                    else if(scope.mode === 'edit'){
                        for(fld in scope.survey_questions){
                            if(scope.survey_questions[fld].variable === scope.variable && fld!==key){
                                scope.duplicate = true;
                            }
                        }
                    }

                }

                if(scope.duplicate===true || scope.invalidChoice===true || scope.minTextError === true || scope.maxTextError === true){
                    return;
                }

                try {
                    //create data object for each submitted question
                    data.question_name = scope.question_name;
                    data.question_description = (scope.question_description) ? scope.question_description : "" ;
                    data.required = scope.required;
                    data.type = scope.type.type;
                    data.variable = scope.variable;

                    //set the data.min depending on which type of question
                    if (scope.type.type === 'text') {
                        data.min = scope.text_min;
                    } else if (scope.type.type === 'textarea') {
                        data.min = scope.textarea_min;
                    } else if (scope.type.type === 'password') {
                        data.min = scope.password_min;
                    } else if (scope.type.type === 'float') {
                        data.min = scope.float_min;
                    } else if (scope.type.type === 'integer') {
                        data.min = scope.int_min;
                    } else {
                        data.min = "";
                    }
                    // set hte data max depending on which type
                    if (scope.type.type === 'text') {
                        data.max = scope.text_max;
                    } else if (scope.type.type === 'textarea') {
                        data.max = scope.textarea_max;
                    } else if (scope.type.type === 'password') {
                        data.max = scope.password_max;
                    } else if (scope.type.type === 'float') {
                        data.max = scope.float_max;
                    } else if (scope.type.type === 'integer') {
                        data.max = scope.int_max;
                    } else {
                        data.max = "";
                    }

                    //set the data.default depending on which type
                    if (scope.type.type === 'text' || scope.type.type === 'multiplechoice') {
                        data.default = scope.default;
                    } else if (scope.type.type === 'textarea') {
                        data.default = scope.default_textarea;
                    } else if (scope.type.type === 'password') {
                        data.default = scope.default_password;
                    } else if (scope.type.type === 'multiselect') {
                          data.default = scope.default_multiselect;
                    } else if (scope.type.type === 'float') {
                        data.default = scope.default_float;
                    } else if (scope.type.type === 'integer') {
                        data.default = scope.default_int;
                    } else {
                        data.default = "";
                    }
                    data.choices = (scope.type.type === "multiplechoice") ? scope.choices : (scope.type.type === 'multiselect') ? scope.choices : "" ;

                    Wait('stop');
                    if(scope.mode === 'add' || scope.mode==="edit" && scope.can_edit === true){
                        $('#survey-save-button').removeAttr('disabled');
                    }

                    if(GenerateForm.mode === 'add'){
                        if(scope.mode === 'add'){
                            questions.push(data);
                            $('#new_question .aw-form-well').remove();
                            $('#add_question_btn').show();
                            scope.finalizeQuestion(data , questions.length-1);
                        }
                        else if (scope.mode === 'edit'){
                            scope.survey_questions.push(data);
                            $('#new_question .aw-form-well').remove();
                            $('#add_question_btn').show();
                            scope.finalizeQuestion(data , scope.survey_questions.length-1);
                        }

                    }
                    if(GenerateForm.mode === 'edit'){
                        elementID = event.target.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.id;
                        key = elementID.split('_')[1];
                        if(scope.mode==='add'){
                            questions[key] = data;
                        }
                        else if(scope.mode === 'edit'){
                            scope.survey_questions[key] = data;
                        }
                        $('#'+elementID).empty();
                        scope.finalizeQuestion(data , key);
                    }



                } catch (err) {
                    Wait('stop');
                    Alert("Error", "Error parsing extra variables. Parser returned: " + err);
                }
            };
            scope.resetForm = function(){
                html = '<div class="row">'+
                        '<div class="col-sm-12">'+
                        '<label for="survey"><span class="label-text prepend-asterisk"> Questions</span></label>'+
                        '<div id="survey_maker_question_area"></div>'+
                        '<div id="finalized_questions"></div>'+
                        '<button style="display:none" type="button" class="btn btn-sm btn-primary" id="add_question_btn" ng-click="addNewQuestion()" aw-tool-tip="Create a new question" data-placement="top" data-original-title="" title="" disabled><i class="fa fa-plus fa-lg"></i>  New Question</button>'+
                        '<div id="new_question"></div>'+
                    '</div>'+
                '</div>';
                $('#survey-modal-dialog').html(html);
                element = angular.element(document.getElementById('add_question_btn'));
                $compile(element)(scope);
            };

            scope.saveSurvey = function() {
                Wait('start');
                if(scope.mode ==="add"){
                    $('#survey-modal-dialog').dialog('close');
                    if(questions.length>0){
                        scope.survey_questions = questions;
                    }
                    scope.survey_name = "";
                    scope.survey_description = "";
                    questions = [] ;
                    scope.$emit('SurveySaved');
                }
                else{
                    scope.survey_name = "";
                    scope.survey_description = "";
                    url = GetBasePath('job_templates') + id + '/survey_spec/';
                    Rest.setUrl(url);
                    Rest.post({ name: scope.survey_name, description: scope.survey_description, spec: scope.survey_questions })
                        .success(function () {
                            // Wait('stop');
                            $('#survey-modal-dialog').dialog('close');
                            scope.$emit('SurveySaved');
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to add new survey. POST returned status: ' + status });
                        });
                }
            };

            //for toggling the input on password inputs
            scope.toggleInput = function(id) {
                var buttonId = id + "_show_input_button",
                    inputId = id,
                    buttonInnerHTML = $(buttonId).html();
                if (buttonInnerHTML.indexOf("Show") > -1) {
                    $(buttonId).html("Hide");
                    $(inputId).attr("type", "text");
                } else {
                    $(buttonId).html("Show");
                    $(inputId).attr("type", "password");
                }
            };

        };
    }

Init.$inject =
    [   '$location',
        'deleteSurvey',
        'editSurvey',
        'addSurvey',
        'GenerateForm',
        'questionDefinitionForm',
        'Wait',
        'Alert',
        'GetBasePath',
        'Rest',
        'ProcessErrors',
        '$compile',
        'finalizeQuestion',
        'editQuestion',
        '$sce'
    ];
