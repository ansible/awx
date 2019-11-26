/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$filter', '$state', '$stateParams', '$http', 'Wait',
    '$scope', '$rootScope', 'CreateSelect2', 'ParseTypeChange', 'GetBasePath',
    'Rest', 'ParentObject', 'JobTemplateModel', '$q', 'Empty', 'SchedulePost',
    'ProcessErrors', 'SchedulerInit', '$location', 'PromptService', 'RRuleToAPI', 'moment',
    'WorkflowJobTemplateModel', 'SchedulerStrings', 'rbacUiControlService', 'Alert',
    function($filter, $state, $stateParams, $http, Wait,
        $scope, $rootScope, CreateSelect2, ParseTypeChange, GetBasePath,
        Rest, ParentObject, JobTemplate, $q, Empty, SchedulePost,
        ProcessErrors, SchedulerInit, $location, PromptService, RRuleToAPI, moment,
        WorkflowJobTemplate, SchedulerStrings, rbacUiControlService, Alert
    ) {

    var base = $scope.base || $location.path().replace(/^\//, '').split('/')[0],
        scheduler,
        job_type;

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
        launchConf.variables_needed_to_start.length !== 0;

    var schedule_url = ParentObject.related.schedules || `${ParentObject.related.inventory_source}schedules`;
    if (ParentObject){
        $scope.parentObject = ParentObject;
        let scheduleEndpoint = ParentObject.endpoint|| ParentObject.related.schedules || `${ParentObject.related.inventory_source}schedules`;
        $scope.canAdd = false;
        rbacUiControlService.canAdd(scheduleEndpoint)
            .then(function(params) {
                $scope.canAdd = params.canAdd;
            });
    }

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

    $scope.preventCredsWithPasswords = true;
    $scope.strings = SchedulerStrings;

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
        SchedulePost({
            scope: $scope,
            url: schedule_url,
            scheduler: scheduler,
            promptData: $scope.promptData,
            mode: 'add'
        }).then(() => {
            Wait('stop');
            $state.go("^", null, {reload: true});
        });
    };

    $scope.prompt = () => {
        $scope.promptData.triggerModalOpen = true;
    };

    $scope.formCancel = function() {
        $state.go("^");
    };

    // initial end @ midnight values
    $scope.schedulerEndHour = "00";
    $scope.schedulerEndMinute = "00";
    $scope.schedulerEndSecond = "00";
    $scope.parentObject = ParentObject;
    
    $scope.hideForm = true;

    // extra_data field is not manifested in the UI when scheduling a Management Job
    if ($state.current.name === 'templates.editJobTemplate.schedules.add'){
        $scope.parseType = 'yaml';

        let jobTemplate = new JobTemplate();

        $q.all([jobTemplate.optionsLaunch(ParentObject.id), jobTemplate.getLaunch(ParentObject.id)])
            .then((responses) => {
                let launchConf = responses[1].data;

                if (launchConf.passwords_needed_to_start &&
                    launchConf.passwords_needed_to_start.length > 0 &&
                    !launchConf.ask_credential_on_launch
                ) {
                    Alert(SchedulerStrings.get('form.WARNING'), SchedulerStrings.get('form.CREDENTIAL_REQUIRES_PASSWORD_WARNING'), 'alert-info');
                    $state.go('^', { reload: true });
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

                if (launchConf.ask_variables_on_launch) {
                    $scope.extraVars = ParentObject.extra_vars === '' ? '---' : ParentObject.extra_vars;

                    ParseTypeChange({
                        scope: $scope,
                        variable: 'extraVars',
                        parse_variable: 'parseType',
                        field_id: 'SchedulerForm-extraVars'
                    });
                } else {
                    $scope.noVars = true;
                }

                if (!shouldShowPromptButton(launchConf)) {
                        $scope.showPromptButton = false;
                } else {
                    $scope.showPromptButton = true;

                    // Ignore the fact that variables might be promptable on launch
                    // Promptable variables will happen in the schedule form
                    launchConf.ignore_ask_variables = true;

                    if (launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory')) {
                        $scope.promptModalMissingReqFields = true;
                    }

                    if (launchConf.survey_enabled) {
                        // go out and get the survey questions
                        jobTemplate.getSurveyQuestions(ParentObject.id)
                            .then((surveyQuestionRes) => {

                                let processed = PromptService.processSurveyQuestions({
                                    surveyQuestions: surveyQuestionRes.data.spec
                                });

                                $scope.missingSurveyValue = processed.missingSurveyValue;

                                $scope.promptData = {
                                    launchConf: responses[1].data,
                                    launchOptions: responses[0].data,
                                    surveyQuestions: processed.surveyQuestions,
                                    template: ParentObject.id,
                                    prompts: PromptService.processPromptValues({
                                        launchConf: responses[1].data,
                                        launchOptions: responses[0].data
                                    }),
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
                        $scope.promptData = {
                            launchConf: responses[1].data,
                            launchOptions: responses[0].data,
                            template: ParentObject.id,
                            prompts: PromptService.processPromptValues({
                                launchConf: responses[1].data,
                                launchOptions: responses[0].data
                            }),
                        };

                        watchForPromptChanges();
                    }
                }
            });
    } else if ($state.current.name === 'templates.editWorkflowJobTemplate.schedules.add'){
        $scope.parseType = 'yaml';
        let workflowJobTemplate = new WorkflowJobTemplate();

        $q.all([workflowJobTemplate.optionsLaunch(ParentObject.id), workflowJobTemplate.getLaunch(ParentObject.id)])
            .then((responses) => {
                let launchConf = responses[1].data;

                let watchForPromptChanges = () => {
                    $scope.$watch('missingSurveyValue', function() {
                        $scope.promptModalMissingReqFields = $scope.missingSurveyValue ? true : false;
                    });
                };

                if (launchConf.ask_variables_on_launch) {
                    $scope.noVars = false;
                    $scope.extraVars = ParentObject.extra_vars === '' ? '---' : ParentObject.extra_vars;

                    ParseTypeChange({
                        scope: $scope,
                        variable: 'extraVars',
                        parse_variable: 'parseType',
                        field_id: 'SchedulerForm-extraVars'
                    });
                } else {
                    $scope.noVars = true;
                }

                if (!shouldShowPromptButton(launchConf)) {
                    $scope.showPromptButton = false;
                } else {
                    $scope.showPromptButton = true;

                    if(launchConf.survey_enabled) {
                        // go out and get the survey questions
                        workflowJobTemplate.getSurveyQuestions(ParentObject.id)
                            .then((surveyQuestionRes) => {

                                let processed = PromptService.processSurveyQuestions({
                                    surveyQuestions: surveyQuestionRes.data.spec
                                });

                                $scope.missingSurveyValue = processed.missingSurveyValue;

                                $scope.promptData = {
                                    launchConf: responses[1].data,
                                    launchOptions: responses[0].data,
                                    surveyQuestions: processed.surveyQuestions,
                                    templateType: ParentObject.type,
                                    template: ParentObject.id,
                                    prompts: PromptService.processPromptValues({
                                        launchConf: responses[1].data,
                                        launchOptions: responses[0].data
                                    }),
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
                            launchConf: responses[1].data,
                            launchOptions: responses[0].data,
                            templateType: ParentObject.type,
                            template: ParentObject.id,
                            prompts: PromptService.processPromptValues({
                                launchConf: responses[1].data,
                                launchOptions: responses[0].data
                            }),
                        };

                        watchForPromptChanges();
                    }
                }
            });
    }

    if ($state.current.name === 'templates.editWorkflowJobTemplate.schedules.add' ||
        $state.current.name === 'projects.edit.schedules.add' ||
        $state.current.name === 'inventories.edit.inventory_sources.edit.schedules.add'
    ){
        $scope.noVars = true;
    }

    job_type = $scope.parentObject.job_type;
    if (!Empty($stateParams.id) && base !== 'system_job_templates' && base !== 'inventories' && !schedule_url) {
        schedule_url = GetBasePath(base) + $stateParams.id + '/schedules/';
    } else if (base === "inventories"){
        if (!schedule_url){
            Rest.setUrl(GetBasePath('groups') + $stateParams.id + '/');
            Rest.get()
            .then(function (data) {
                    schedule_url = data.data.related.inventory_source + 'schedules/';
                }).catch(function (response) {
                ProcessErrors(null, response.data, response.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to get inventory group info. GET returned status: ' +
                    response.status
                });
            });
        }
    } else if (base === 'system_job_templates') {
        schedule_url = GetBasePath(base) + $stateParams.id + '/schedules/';
        let parentJobType = _.get($scope.parentObject, 'job_type');
        if (parentJobType !== 'cleanup_tokens' && parentJobType !== 'cleanup_sessions') {
            $scope.askDaysToKeep = true;
        }
    }

    Wait('start');
    $('#form-container').empty();
    scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false });
    let timeZonesAPI = () => {
        return $http.get(`/api/v2/schedules/zoneinfo/`);
    };
    // set API timezones to scheduler object
    timeZonesAPI().then(({data}) => {
        scheduler.scope.timeZones = data;
        scheduler.scope.schedulerTimeZone = _.find(data, (zone) => {
            return zone.name === scheduler.scope.current_timezone.name;
        });
        $scope.scheduleTimeChange();
    });
    if ($scope.schedulerUTCTime) {
        // The UTC time is already set
        $scope.processSchedulerEndDt();
    } else {
        // We need to wait for it to be set by angular-scheduler because the following function depends
        // on it
        var schedulerUTCTimeWatcher = $scope.$watch('schedulerUTCTime', function(newVal) {
            if (newVal) {
                // Remove the watcher
                schedulerUTCTimeWatcher();
                $scope.processSchedulerEndDt();
            }
        });
    }

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

    scheduler.inject('form-container', false);
    scheduler.injectDetail('occurrences', false);
    scheduler.clear();
    $scope.$on("htmlDetailReady", function() {
        $scope.hideForm = false;
        scheduler.scope.schedulerStartDt = moment(new Date()).add(1,'days');

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
            "schedularEndSecond"
        ], function() {
            $rootScope.$broadcast("loadSchedulerDetailPane");
        }, true);

        $scope.$watch("weekDays", function() {
            $rootScope.$broadcast("loadSchedulerDetailPane");
        }, true);

        Wait('stop');
    });
    $scope.showRRuleDetail = false;

    $('#scheduler-tabs li a').on('shown.bs.tab', function(e) {
        if ($(e.target).text() === 'Details') {
            if (!scheduler.isValid()) {
                $('#scheduler-tabs a:first').tab('show');
            }
        }
    });

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
    callSelect2();
}];
