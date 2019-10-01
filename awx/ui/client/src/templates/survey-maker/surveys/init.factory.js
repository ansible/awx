export default
        function Init(DeleteSurvey, EditSurvey, AddSurvey, GenerateForm, SurveyQuestionForm, Wait, Alert,
            GetBasePath, Rest, ProcessErrors, EditQuestion, CreateSelect2, i18n) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                form = SurveyQuestionForm,
                sce = params.sce,
                templateType = params.templateType;
            scope.sce = sce;
            scope.survey_questions = [];
            scope.answer_types=[
                {name: i18n._('Text'), type: 'text'},
                {name: i18n._('Textarea'), type: 'textarea'},
                {name: i18n._('Password'), type: 'password'},
                {name: i18n._('Multiple Choice (single select)'), type: 'multiplechoice'},
                {name: i18n._('Multiple Choice (multiple select)'), type: 'multiselect'},
                {name: i18n._('Integer'), type: 'integer'},
                {name: i18n._('Float'), type: 'float'}
            ];
            scope.disableSurveyTooltip = i18n._('Disable Survey');
            scope.editQuestionTooltip = i18n._('Edit Question');
            scope.deleteQuestionTooltip = i18n._('Delete Question');
            scope.dragQuestionTooltip = i18n._('Drag to reorder question');

            /* SURVEY RELATED FUNCTIONS */

            // Called when a job template does not have a saved survey.  This simply sets some
            // default variables and fills the add question form via form generator.
            scope.addSurvey = function() {
                AddSurvey({
                    scope: scope
                });
            };

            // Called when a job template (new or existing) already has a "saved" survey
            // In the case where a job template has not yet been created but a survey has
            // been the data is just pulled out of the scope rather than from the server.
            // (this is dictated by scope.mode)
            scope.editSurvey = function() {
                // Goes out and fetches the existing survey and populates the preview
                EditSurvey({
                    scope: scope,
                    id: id,
                    templateType: templateType
                });
            };

            // This gets called after a user confirms survey deletion
            scope.deleteSurvey = function() {
                    // Hide the delete overlay
                    scope.hideDeleteOverlay();
                    // Show the loading spinner
                    Wait('start');
                    // Call the delete survey factory which handles making the rest call
                    // and closing the modal after success
                    DeleteSurvey({
                        scope: scope,
                        id: id,
                        templateType: templateType
                    });
            };

            // Called when the user hits cancel/close on the survey modal.  This function
            // goes out and cleans up the survey_questions on scope before destroying
            // the modal.
            scope.closeSurvey = function(id) {
                // Clear out the whole array, this data gets pulled in each time the modal is opened
                scope.survey_questions = [];

                $('#' + id).dialog('destroy');
            };

            scope.saveSurvey = function() {
                Wait('start');

                scope.survey_name = "";
                scope.survey_description = "";

                var updateSurveyQuestions = function() {
                    if(templateType === 'job_template') {
                        Rest.setUrl(GetBasePath('job_templates') + id + '/survey_spec/');
                    }
                    else if(templateType === 'workflow_job_template') {
                        Rest.setUrl(GetBasePath('workflow_job_templates') + id + '/survey_spec/');
                    }
                    return Rest.post({name: scope.survey_name, description: scope.survey_description, spec: scope.survey_questions })
                    .then(() => {

                    })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to add new survey. POST returned status: ' + status });
                    });
                };

                var updateSurveyEnabled = function() {
                    if(templateType === 'job_template') {
                        Rest.setUrl(GetBasePath('job_templates') + id+ '/');
                    }
                    else if(templateType === 'workflow_job_template') {
                        Rest.setUrl(GetBasePath('workflow_job_templates') + id+ '/');
                    }
                    return Rest.patch({"survey_enabled": scope.survey_enabled})
                    .then(() => {

                    })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, form, {
                            hdr: 'Error!',
                            msg: 'Failed to save survey_enabled: GET status: ' + status
                        });
                    });
                };

                if (!scope.survey_questions || scope.survey_questions.length === 0) {
                    scope.deleteSurvey();
                } else {
                    updateSurveyQuestions()
                    .then(function() {
                        return updateSurveyEnabled();
                    })
                    .then(function() {
                        scope.closeSurvey('survey-modal-dialog');
                        scope.$emit('SurveySaved');
                    });
                }
            };

            // Gets called when the user clicks the on/off toggle beside the survey modal title.
            scope.toggleSurveyEnabled = function() {
                scope.survey_enabled = !scope.survey_enabled;
            };

            /* END SURVEY RELATED FUNCTIONS */

            /* QUESTION RELATED FUNCTIONS */

            // This injects the Add Question form into survey_maker_question_form
            scope.generateAddQuestionForm = function(){
                // This tmpMode logic is necessary because form generator seems to set scope.mode to match the mode that you pass it.
                // So if a user is editing a job template (scope.mode='edit') but the JT doesn't have a survey then when we open the
                // modal we need to make sure that scope.mode is still 'edit' after the Add Question form is injected.
                // To avoid having to do this we'd need to track the job template mode in a variable other than scope.mode.
                var tmpMode = scope.mode;
                GenerateForm.inject(form, { id:'survey_maker_question_form', mode: 'add' , scope: scope, related: false, noPanel: true});
                scope.mode = tmpMode;
                scope.clearQuestion();
            };

            // This gets called when a users clicks the pencil icon beside a question preview in order to edit it.
            scope.editQuestion = function(index){
                scope.duplicate = false;
                // The edit question factory injects the edit form and fills the form with the question data from memory.
                EditQuestion({
                    index: index,
                    scope: scope,
                    question: scope.survey_questions[index]
                });
            };

            // Gets called when a user clicks the delete icon on a question in the survey preview
            scope.showDeleteQuestion = function(deleteIndex) {
                // Keep track of the question to be deleted on scope
                scope.questionToBeDeleted = deleteIndex;
                // Show the delete overlay with mode='question'
                scope.showDeleteOverlay('question');
            };

            // Called after a user confirms question deletion (hitting the DELETE button on the delete question overlay).
            scope.deleteQuestion = function(index){
                // Move the edit question index down by one if this question came before the
                // one being edited in the array.  This makes sure that our pointer to the question
                // currently being edited gets updated independently from a deleted question.
                if(GenerateForm.mode === 'edit' && !isNaN(scope.editQuestionIndex)){
                    if(scope.editQuestionIndex === index) {
                        // The user is deleting the question being edited - need to roll back to Add Question mode
                        scope.editQuestionIndex = null;
                        scope.generateAddQuestionForm();
                    }
                    else if(scope.editQuestionIndex > index) {
                        scope.editQuestionIndex--;
                    }
                }
                // Remove the question from the array
                scope.survey_questions.splice(index, 1);
                // Hide the delete overlay
                scope.hideDeleteOverlay();
            };

            function clearTypeSpecificFields() {
                scope.minTextError = false;
                scope.maxTextError = false;
                scope.default = "";
                scope.default_multiselect = "";
                scope.default_float = "";
                scope.default_int = "";
                scope.default_textarea = "";
                scope.default_password = "" ;
                scope.choices = "";
                scope.text_min = 0;
                scope.text_max = 1024 ;
                scope.textarea_min = 0;
                scope.textarea_max = 4096;
                scope.password_min = 0;
                scope.password_max = 32;
                scope.int_min = 0;
                scope.int_max = 100;
                scope.float_min = 0.0;
                scope.float_max = 100.0;
            }

            // Sets all of our scope variables used for adding/editing a question back to a clean state
            scope.clearQuestion = function(){
                clearTypeSpecificFields();
                scope.editQuestionIndex = null;
                scope.question_name = null;
                scope.question_description = null;
                scope.variable = null;
                scope.required = true; //set the required checkbox to true via the ngmodel attached to scope.required.
                scope.duplicate = false;
                scope.invalidChoice = false;
                scope.type = "";

                // Make sure that the select2 dropdown for question type is clean
                CreateSelect2({
                    element:'#survey_question_type',
                    multiple: false
                });

                // Set the whole form to pristine
                scope.survey_question_form.$setPristine();
            };

            // Gets called when the "type" dropdown value changes.  In that case, we want to clear out
            // all the "type" specific fields/errors and start fresh.
            scope.typeChange = function() {
                clearTypeSpecificFields();
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

            // Function that gets called when a user hits ADD/UPDATE on the survey question form.  This
            // function handles some validation as well as eventually adding the question to the
            // scope.survey_questions array.
            scope.submitQuestion = function(){
                var data = {},
                fld, i,
                choiceArray,
                answerArray;
                scope.invalidChoice = false;
                scope.duplicate = false;
                scope.minTextError = false;
                scope.maxTextError = false;

                if(scope.type.type==="text"){
                    if(scope.default && scope.default.trim() !== ""){
                        if(scope.default.trim().length < scope.text_min &&
                           scope.text_min !== "" &&
                           scope.text_min !== null ){
                               scope.minTextError = true;
                        }
                        if(scope.text_max < scope.default.trim().length &&
                           scope.text_max !== "" &&
                           scope.text_max !== null ){
                               scope.maxTextError = true;
                        }
                    }
                }

                if(scope.type.type==="textarea"){
                    if(scope.default_textarea && scope.default_textarea.trim() !== ""){
                        if(scope.default_textarea.trim().length < scope.textarea_min &&
                           scope.textarea_min !== "" &&
                           scope.textarea_min !== null ){
                               scope.minTextError = true;
                        }
                        if(scope.textarea_max <  scope.default_textarea.trim().length &&
                           scope.textarea_max !== "" &&
                           scope.textarea_max !== null ){
                               scope.maxTextError = true;
                        }
                    }
                }

                if(scope.type.type==="password"){
                    if(scope.default_password && scope.default_password.trim() !== ""){
                        if(scope.default_password.trim().length < scope.password_min &&
                           scope.password_min !== "" &&
                           scope.password_min !== null ){
                               scope.minTextError = true;
                        }
                        if(scope.password_max <  scope.default_password.trim().length &&
                           scope.password_max !== "" &&
                           scope.password_max !== null ){
                               scope.maxTextError = true;
                        }
                    }
                }

                if(scope.type.type==="multiselect" && scope.default_multiselect && scope.default_multiselect.trim() !== ""){
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

                if(scope.type.type==="multiplechoice" && scope.default && scope.default.trim() !== ""){
                    choiceArray = scope.choices.split(/\n/);
                    if($.inArray(scope.default, choiceArray)===-1){
                        scope.invalidChoice = true;
                    }
                }

                // validate that there aren't any questions using this var name.
                if(GenerateForm.mode === 'add'){
                    for(fld in scope.survey_questions){
                        if(scope.survey_questions[fld].variable === scope.variable){
                            scope.duplicate = true;
                        }
                    }
                }
                if(GenerateForm.mode === 'edit'){
                    // Loop across the survey questions and see if a different question already has
                    // the same variable name
                    for( i=0; i<scope.survey_questions.length; i++){
                        if(scope.survey_questions[i].variable === scope.variable && i!==scope.editQuestionIndex){
                            scope.duplicate = true;
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
                        data.min = parseInt(scope.text_min);
                    } else if (scope.type.type === 'textarea') {
                        data.min = parseInt(scope.textarea_min);
                    } else if (scope.type.type === 'password') {
                        data.min = parseInt(scope.password_min);
                    } else if (scope.type.type === 'float') {
                        data.min = parseFloat(scope.float_min);
                    } else if (scope.type.type === 'integer') {
                        data.min = parseInt(scope.int_min);
                    } else {
                        data.min = null;
                    }
                    // set hte data max depending on which type
                    if (scope.type.type === 'text') {
                        data.max = parseInt(scope.text_max);
                    } else if (scope.type.type === 'textarea') {
                        data.max = parseInt(scope.textarea_max);
                    } else if (scope.type.type === 'password') {
                        data.max = parseInt(scope.password_max);
                    } else if (scope.type.type === 'float') {
                        data.max = parseFloat(scope.float_max);
                    } else if (scope.type.type === 'integer') {
                        data.max = parseInt(scope.int_max);
                    } else {
                        data.max = null;
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
                    } else if (scope.type.type === 'float' &&
                        scope.default_float !== '' &&
                        scope.default_float !== null) {
                        data.default = scope.default_float;
                    } else if (scope.type.type === 'integer' &&
                        scope.default_int !== '' &&
                        scope.default_int !== null) {
                        data.default = scope.default_int;
                    } else {
                        data.default = "";
                    }
                    data.choices = (scope.type.type === "multiplechoice") ? scope.choices : (scope.type.type === 'multiselect') ? scope.choices : "" ;

                    if (data.choices !== "") {
                        // remove duplicates from the choices
                        data.choices = _.uniq(data.choices.split("\n")).join("\n");
                    }

                    Wait('stop');

                    if(GenerateForm.mode === 'add'){
                        // Flag this question as new
                        data.new_question = true;

                        scope.survey_questions.push(data);
                        $('#new_question .aw-form-well').remove();
                        $('#add_question_btn').show();
                    }
                    if(GenerateForm.mode === 'edit'){
                        // Overwrite the survey question with the new data
                        scope.survey_questions[scope.editQuestionIndex] = data;
                    }

                    // Throw the user back to the "add question" form
                    scope.generateAddQuestionForm();


                } catch (err) {
                    Wait('stop');
                    Alert("Error", "Error parsing extra variables. Parser returned: " + err);
                }
            };

            // This function is bound to the dnd-drop directive.  When a question is dragged and
            // dropped, this is the function that gets called.
            scope.surveyQuestionDropped = function(dropIndex, question) {

                // Handle moving the question to its new slot in scope.survey_questions
                for(var i=0; i<scope.survey_questions.length; i++) {

                    if(angular.equals(scope.survey_questions[i], question)) {

                        // Check to make sure that the survey question was actually moved
                        if(i !== dropIndex) {
                            // Since the suvey question being "moved" is still technically in the array
                            // we need to adjust the drop index when moving a question down in the array
                            // See: https://github.com/marceljuenemann/angular-drag-and-drop-lists/issues/54#issuecomment-125487293
                            if(i < dropIndex) {
                                dropIndex--;
                            }
                            // Remove this survey question from its original position
                            scope.survey_questions.splice(i, 1);

                            // Add this survey question to its new position
                            scope.survey_questions.splice(dropIndex, 0, question);

                            // Update the editQuestionIndex if applicable
                            if(typeof scope.editQuestionIndex === "number") {
                                // A question is being edited - lets see if we need to adjust the index
                                if(scope.editQuestionIndex === i) {
                                    // The edited question was moved
                                    scope.editQuestionIndex = dropIndex;
                                }
                                else if(scope.editQuestionIndex < i && dropIndex <= scope.editQuestionIndex) {
                                    // An element that was behind the edit question is now ahead of it
                                    scope.editQuestionIndex++;
                                }
                                else if(scope.editQuestionIndex > i && dropIndex >= scope.editQuestionIndex) {
                                    // An element that was ahead of the edit question is now behind it
                                    scope.editQuestionIndex--;
                                }
                            }
                        }

                        // Break out of the for loop
                        break;
                    }

                }

                // return true here signals that the drop is allowed, but that we've already taken care of inserting the element
                return true;
            };

            // Gets called when a user is creating/editing a question that has a password
            // field.  The password field in the form has a SHOW/HIDE button that calls this.
            scope.toggleInput = function(id) {
                // Note that the id string passed into this function will have a "#" prepended
                var buttonId = id + "_show_input_button",
                    inputId = id,
                    buttonInnerHTML = $(buttonId).html();
                if (buttonInnerHTML.indexOf("SHOW") > -1) {
                    $(buttonId).html(i18n._("HIDE"));
                    $(inputId).attr("type", "text");
                } else {
                    $(buttonId).html(i18n._("SHOW"));
                    $(inputId).attr("type", "password");
                }
            };

            /* END QUESTION RELATED FUNCTIONS */

            /* DELETE OVERLAY RELATED FUNCTIONS */

            // This handles setting the delete mode and flipping the boolean used to show the delete overlay
            scope.showDeleteOverlay = function(mode) {
                // Set the delete mode (question or survey) so that the overlay knows
                // how to phrase the prompt
                scope.deleteMode = mode;
                // Flip the deleteOverlayVisible flag so that the overlay becomes visible via ng-show
                scope.deleteOverlayVisible = true;
            };

            // Called by the cancel/close buttons on the delete overlay.  Also called after deletion has been confirmed.
            scope.hideDeleteOverlay = function() {
                // Clear out the delete mode for next time
                scope.deleteMode = null;
                // Clear out the index variable for next time
                scope.questionToBeDeleted = null;
                // Hide the delete overlay
                scope.deleteOverlayVisible = false;
            };

            /* END DELETE OVERLAY RELATED FUNCTIONS */

            // Watcher that updates the survey enabled/disabled tooltip based on scope.survey_enabled
            scope.$watch('survey_enabled', function(newVal) {
                scope.surveyEnabledTooltip = (newVal) ? i18n._("Disable survey") : i18n._("Enable survey");
            });

        };
    }

Init.$inject =
    [   'deleteSurvey',
        'editSurvey',
        'addSurvey',
        'GenerateForm',
        'questionDefinitionForm',
        'Wait',
        'Alert',
        'GetBasePath',
        'Rest',
        'ProcessErrors',
        'editQuestion',
        'CreateSelect2',
        'i18n'
    ];
