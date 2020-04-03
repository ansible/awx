export default ['$filter', '$state', '$stateParams', 'Wait', '$scope', 'moment',
'$rootScope', '$http', 'CreateSelect2', 'ParseTypeChange', 'ParentObject', 'ProcessErrors', 'Rest',
'GetBasePath', 'SchedulerInit', 'SchedulePost', 'JobTemplateModel', '$q', 'Empty', 'PromptService', 'RRuleToAPI',
'WorkflowJobTemplateModel', 'SchedulerStrings', 'scheduleResolve', 'timezonesResolve', 'Alert',
function($filter, $state, $stateParams, Wait, $scope, moment,
    $rootScope, $http, CreateSelect2, ParseTypeChange, ParentObject, ProcessErrors, Rest,
    GetBasePath, SchedulerInit, SchedulePost, JobTemplate, $q, Empty, PromptService, RRuleToAPI,
    WorkflowJobTemplate, SchedulerStrings, scheduleResolve, timezonesResolve, Alert
) {

    let schedule, scheduler, scheduleCredentials = [];

    /*
     * Normally if "ask_*" checkboxes are checked in a job template settings,
     * shouldShowPromptButton() returns True to show the "PROMPT" button.
     * However, extra_vars("ask_variables_on_launch") does not use this and
     * displays a separate text area within the add/edit page for input.
     * We exclude "ask_variables_on_launch" from shouldShowPromptButton() here.
     */
    const shouldShowPromptButton = (launchConf) => launchConf.survey_enabled ||
        launchConf.ask_inventory_on_launch ||
        launchConf.ask_credential_on_launch ||
        launchConf.ask_verbosity_on_launch ||
        launchConf.ask_job_type_on_launch ||
        launchConf.ask_limit_on_launch ||
        launchConf.ask_tags_on_launch ||
        launchConf.ask_skip_tags_on_launch ||
        launchConf.ask_diff_mode_on_launch ||
        launchConf.credential_needed_to_start ||
        launchConf.ask_scm_branch_on_launch ||
        launchConf.passwords_needed_to_start.length !== 0 ||
        launchConf.variables_needed_to_start.length !== 0;

    $scope.preventCredsWithPasswords = true;

    // initial end @ midnight values
    $scope.schedulerEndHour = "00";
    $scope.schedulerEndMinute = "00";
    $scope.schedulerEndSecond = "00";
    $scope.parentObject = ParentObject;
    $scope.isEdit = true;
    $scope.hideForm = true;
    $scope.parseType = 'yaml';

    $scope.strings = SchedulerStrings;

    /*
    * Keep processSchedulerEndDt method on the $scope
    * because angular-scheduler references it
    */
    $scope.processSchedulerEndDt = function(){
        // set the schedulerEndDt to be equal to schedulerStartDt + 1 day @ midnight
        var dt = new Date($scope.schedulerUTCTime);
        // increment date by 1 day
        dt.setDate(dt.getDate() + 1);
        var month = $filter('schZeroPad')(dt.getMonth() + 1, 2),
            day = $filter('schZeroPad')(dt.getDate(), 2);
        $scope.$parent.schedulerEndDt = month + '/' + day + '/' + dt.getFullYear();
    };

    $scope.formCancel = function() {
        $state.go("^");
    };

    /*
     * This is a workaround for the angular-scheduler library inserting `ll` into fields after an
     * invalid entry and never unsetting them. Presumably null is being truncated down to 2 chars
     * in that case.
     *
     * Because this same problem exists in the edit mode and because there's no inheritence, this
     * block of code is duplicated in both add/edit controllers pending a much needed broader
     * refactoring effort.
     */
    $scope.timeChange = () => {
        if (!Number($scope.schedulerStartHour)) {
            $scope.schedulerStartHour = '00';
        }

        if (!Number($scope.schedulerStartMinute)) {
            $scope.schedulerStartMinute = '00';
        }

        if (!Number($scope.schedulerStartSecond)) {
            $scope.schedulerStartSecond = '00';
        }

        $scope.scheduleTimeChange();
    };

    $scope.saveSchedule = function() {
        schedule.extra_data = $scope.extraVars;
        SchedulePost({
            scope: $scope,
            url: GetBasePath('schedules') + parseInt($stateParams.schedule_id) + '/',
            scheduler: scheduler,
            mode: 'edit',
            schedule: schedule,
            promptData: $scope.promptData,
            priorCredentials: scheduleCredentials
        }).then(() => {
            Wait('stop');
            $state.go("^", null, {reload: true});
        });
    };

    $scope.prompt = () => {
        $scope.promptData.triggerModalOpen = true;
    };

    var callSelect2 = function() {
        CreateSelect2({
            element: '.MakeSelect2',
            multiple: false
        });
        $("#schedulerTimeZone").select2({
            width:'100%',
            containerCssClass: 'Form-dropDown',
            placeholder: 'SEARCH'
        });
    };

    $scope.$on("updateSchedulerSelects", function() {
        callSelect2();
    });

    let previewList = _.debounce(function(req) {
        $http.post('/api/v2/schedules/preview/', {'rrule': req})
            .then(({data}) => {
                $scope.preview_list = data;
                let parsePreviewList = (tz) => {
                    return data[tz].map(function(date) {
                        date = date.replace(/Z/, '');
                        return moment.parseZone(date).format("MM-DD-YYYY HH:mm:ss");
                    });
                };
                for (let tz in data) {
                    $scope.preview_list.isEmpty = data[tz].length === 0;
                    $scope.preview_list[tz] = parsePreviewList(tz);
                }
            });
    }, 300);

    $scope.$on("setPreviewPane", (event) => {
        let rrule = event.currentScope.rrule.toString();
        let req = RRuleToAPI(rrule, $scope);
        previewList(req);
    });

    Wait('start');

    //sets the timezone dropdown to the timezone specified by the API
    function setTimezone () {
        $scope.schedulerTimeZone = _.find($scope.timeZones, function(x) {
            return x.name === scheduleResolve.timezone;
        });
    }

    // sets the UNTIL portion of the schedule form after the angular-scheduler
    // sets it, but this function reads the 'until' key/value pair directly
    // from the schedule GET response.
    function setUntil (scheduler) {
        let { until } = scheduleResolve;
        if(until !== ''){
            const date = moment(until);
            const endDt =  moment.parseZone(date).format("MM/DD/YYYY");
            const endHour = date.format('HH');
            const endMinute = date.format('mm');
            const endSecond = date.format('ss');
            scheduler.scope.schedulerEndDt = endDt;
            scheduler.scope.schedulerEndHour = endHour;
            scheduler.scope.schedulerEndMinute = endMinute;
            scheduler.scope.schedulerEndSecond = endSecond;
        }
    }

    function init() {
        schedule = scheduleResolve;

        try {
            schedule.extra_data = JSON.parse(schedule.extra_data);
        } catch(e) {
            // do nothing
        }

        $scope.extraVars = (scheduleResolve.extra_data === '' || _.isEmpty(scheduleResolve.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(scheduleResolve.extra_data);

        if (_.has(schedule, 'summary_fields.unified_job_template.unified_job_type') &&
            schedule.summary_fields.unified_job_template.unified_job_type === 'system_job'){
            let scheduleJobType = _.get(schedule.summary_fields.unified_job_template, 'job_type');
            if (scheduleJobType !== 'cleanup_tokens' && scheduleJobType !== 'cleanup_sessions') {
                $scope.askDaysToKeep = true;
            }
        }

        $scope.schedule_obj = scheduleResolve;

        $('#form-container').empty();
        scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false });

        scheduler.scope.timeZones = timezonesResolve;
        setTimezone();

        scheduler.inject('form-container', false);
        scheduler.injectDetail('occurrences', false);

        if (!/DTSTART/.test(schedule.rrule)) {
            schedule.rrule += ";DTSTART=" + schedule.dtstart.replace(/\.\d+Z$/,'Z');
        }
        schedule.rrule = schedule.rrule.replace(/ RRULE:/,';');
        schedule.rrule = schedule.rrule.replace(/DTSTART:/,'DTSTART=');
        $scope.$on("htmlDetailReady", function() {
            scheduler.setRRule(schedule.rrule);
            scheduler.setName(schedule.name);
            setTimezone();
            setUntil(scheduler);
            $scope.hideForm = false;

            $scope.$watchGroup(["schedulerName",
                "schedulerStartDt",
                "schedulerStartHour",
                "schedulerStartMinute",
                "schedulerStartSecond",
                "schedulerTimeZone",
                "schedulerFrequency",
                "schedulerInterval",
                "monthlyRepeatOption",
                "monthDay",
                "monthlyOccurrence",
                "monthlyWeekDay",
                "yearlyRepeatOption",
                "yearlyMonth",
                "yearlyMonthDay",
                "yearlyOccurrence",
                "yearlyWeekDay",
                "yearlyOtherMonth",
                "schedulerEnd",
                "schedulerOccurrenceCount",
                "schedulerEndDt",
                "schedulerEndHour",
                "schedulerEndMinute",
                "schedulerEndSecond"
            ], function() {
                $rootScope.$broadcast("loadSchedulerDetailPane");
            }, true);

            $scope.$watch("weekDays", function() {
                $rootScope.$broadcast("loadSchedulerDetailPane");
            }, true);

            $rootScope.$broadcast("loadSchedulerDetailPane");
            Wait('stop');
        });

        $scope.showRRuleDetail = false;
        scheduler.setRRule(schedule.rrule);
        scheduler.setName(schedule.name);
        $rootScope.breadcrumb.schedule_name = $scope.schedulerName;
        $rootScope.breadcrumb[`${$scope.parentObject.type}_name`] = $scope.parentObject.name;
        $scope.noVars = true;
        scheduler.scope.timeZones = timezonesResolve;
        scheduler.scope.schedulerTimeZone = scheduleResolve.timezone;
        if ($scope.askDaysToKeep){
            $scope.schedulerPurgeDays = Number(schedule.extra_data.days);
        }

        const codeMirrorExtraVars = () => {
            ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
        };

        if ($state.current.name === 'templates.editJobTemplate.schedules.edit' || $scope.parentObject.type === 'job_template'){

            let jobTemplate = new JobTemplate();

            Rest.setUrl(scheduleResolve.related.credentials);
            $q.all([jobTemplate.optionsLaunch(ParentObject.id), jobTemplate.getLaunch(ParentObject.id), Rest.get()])
                .then((responses) => {
                    let launchOptions = responses[0].data,
                        launchConf = responses[1].data;
                        scheduleCredentials = responses[2].data.results;

                    if (launchConf.passwords_needed_to_start &&
                        launchConf.passwords_needed_to_start.length > 0 &&
                        !launchConf.ask_credential_on_launch
                    ) {
                        Alert(SchedulerStrings.get('form.WARNING'), SchedulerStrings.get('form.CREDENTIAL_REQUIRES_PASSWORD_WARNING'), 'alert-info');
                        $scope.credentialRequiresPassword = true;
                    }

                    let watchForPromptChanges = () => {
                        let promptValuesToWatch = [
                            'promptData.prompts.inventory.value',
                            'promptData.prompts.jobType.value',
                            'promptData.prompts.verbosity.value',
                            'missingSurveyValue'
                        ];

                        $scope.$watchGroup(promptValuesToWatch, function() {
                            let missingPromptValue = false;
                            if ($scope.missingSurveyValue) {
                                missingPromptValue = true;
                            } else if (!$scope.promptData.prompts.inventory.value || !$scope.promptData.prompts.inventory.value.id) {
                                missingPromptValue = true;
                            }
                            $scope.promptModalMissingReqFields = missingPromptValue;
                        });
                    };

                    let prompts = PromptService.processPromptValues({
                        launchConf: responses[1].data,
                        launchOptions: responses[0].data,
                        currentValues: scheduleResolve
                    });

                    let defaultCredsWithoutOverrides = [];

                    const credentialHasScheduleOverride = (templateDefaultCred) => {
                        let credentialHasOverride = false;
                        scheduleCredentials.forEach((scheduleCred) => {
                            if (templateDefaultCred.credential_type === scheduleCred.credential_type) {
                                if (
                                    (!templateDefaultCred.vault_id && !scheduleCred.inputs.vault_id) ||
                                    (templateDefaultCred.vault_id && scheduleCred.inputs.vault_id && templateDefaultCred.vault_id === scheduleCred.inputs.vault_id)
                                ) {
                                    credentialHasOverride = true;
                                }
                            }
                        });

                        return credentialHasOverride;
                    };

                    if (_.has(launchConf, 'defaults.credentials')) {
                        launchConf.defaults.credentials.forEach((defaultCred) => {
                            if (!credentialHasScheduleOverride(defaultCred)) {
                                defaultCredsWithoutOverrides.push(defaultCred);
                            }
                        });
                    }

                    prompts.credentials.value = defaultCredsWithoutOverrides.concat(scheduleCredentials);

                    // the extra vars codemirror is ONLY shown if the
                    // ask_variables_on_launch = true
                    if (launchConf.ask_variables_on_launch) {
                        $scope.noVars = false;
                    } else {
                        $scope.noVars = true;
                    }

                    if (!shouldShowPromptButton(launchConf)) {
                            $scope.showPromptButton = false;

                            if (launchConf.ask_variables_on_launch) {
                                codeMirrorExtraVars();
                            }
                    } else {
                        $scope.showPromptButton = true;

                        // Ignore the fact that variables might be promptable on launch
                        // Promptable variables will happen in the schedule form
                        launchConf.ignore_ask_variables = true;

                        if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has(scheduleResolve, 'summary_fields.inventory')) {
                            $scope.promptModalMissingReqFields = true;
                        }

                        if (responses[1].data.survey_enabled) {
                            // go out and get the survey questions
                            jobTemplate.getSurveyQuestions(ParentObject.id)
                                .then((surveyQuestionRes) => {

                                    let processed = PromptService.processSurveyQuestions({
                                        surveyQuestions: surveyQuestionRes.data.spec,
                                        extra_data: _.cloneDeep(scheduleResolve.extra_data)
                                    });

                                    $scope.missingSurveyValue = processed.missingSurveyValue;

                                    $scope.extraVars = (processed.extra_data === '' || _.isEmpty(processed.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(processed.extra_data);

                                    codeMirrorExtraVars();

                                    $scope.promptData = {
                                        launchConf: launchConf,
                                        launchOptions: launchOptions,
                                        prompts: prompts,
                                        surveyQuestions: surveyQuestionRes.data.spec,
                                        template: ParentObject.id
                                    };

                                    $scope.$watch('promptData.surveyQuestions', () => {
                                        let missingSurveyValue = false;
                                        _.each($scope.promptData.surveyQuestions, (question) => {
                                            if (question.required && (Empty(question.model) || question.model === [])) {
                                                missingSurveyValue = true;
                                            }
                                        });
                                        $scope.missingSurveyValue = missingSurveyValue;
                                    }, true);

                                    watchForPromptChanges();
                                });
                        } else {
                            codeMirrorExtraVars();
                            $scope.promptData = {
                                launchConf: launchConf,
                                launchOptions: launchOptions,
                                prompts: prompts,
                                template: ParentObject.id
                            };
                            watchForPromptChanges();
                        }
                    }
                });
        } else if ($state.current.name === 'templates.editWorkflowJobTemplate.schedules.edit' || $scope.parentObject.type === 'workflow_job_template') {
            let workflowJobTemplate = new WorkflowJobTemplate();

            $q.all([workflowJobTemplate.optionsLaunch(ParentObject.id), workflowJobTemplate.getLaunch(ParentObject.id)])
                .then((responses) => {
                    let launchOptions = responses[0].data,
                        launchConf = responses[1].data;

                    let watchForPromptChanges = () => {
                        $scope.$watch('missingSurveyValue', function() {
                            $scope.promptModalMissingReqFields = $scope.missingSurveyValue ? true : false;
                        });
                    };

                    let prompts = PromptService.processPromptValues({
                        launchConf: responses[1].data,
                        launchOptions: responses[0].data,
                        currentValues: scheduleResolve
                    });

                    // the extra vars codemirror is ONLY shown if the
                    // ask_variables_on_launch = true
                    if (launchConf.ask_variables_on_launch) {
                        $scope.noVars = false;
                        codeMirrorExtraVars();
                    } else {
                        $scope.noVars = true;
                    }

                   if (!shouldShowPromptButton(launchConf)) {
                        $scope.showPromptButton = false;
                    } else {
                        $scope.showPromptButton = true;

                        if(responses[1].data.survey_enabled) {
                            // go out and get the survey questions
                            workflowJobTemplate.getSurveyQuestions(ParentObject.id)
                                .then((surveyQuestionRes) => {

                                    let processed = PromptService.processSurveyQuestions({
                                        surveyQuestions: surveyQuestionRes.data.spec,
                                        extra_data: _.cloneDeep(scheduleResolve.extra_data)
                                    });

                                    $scope.missingSurveyValue = processed.missingSurveyValue;

                                    $scope.promptData = {
                                        launchConf: launchConf,
                                        launchOptions: launchOptions,
                                        prompts: prompts,
                                        surveyQuestions: surveyQuestionRes.data.spec,
                                        templateType: ParentObject.type,
                                        template: ParentObject.id
                                    };

                                    $scope.$watch('promptData.surveyQuestions', () => {
                                        let missingSurveyValue = false;
                                        _.each($scope.promptData.surveyQuestions, (question) => {
                                            if(question.required && (Empty(question.model) || question.model === [])) {
                                                missingSurveyValue = true;
                                            }
                                        });
                                        $scope.missingSurveyValue = missingSurveyValue;
                                    }, true);

                                    watchForPromptChanges();
                                });
                        }
                        else {
                            $scope.promptData = {
                                launchConf: launchConf,
                                launchOptions: launchOptions,
                                prompts: prompts,
                                templateType: ParentObject.type,
                                template: ParentObject.id
                            };
                            watchForPromptChanges();
                        }
                    }
                });

        }
    }

    init();

    callSelect2();
}];
