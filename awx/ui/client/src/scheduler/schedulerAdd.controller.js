/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$filter', '$state', '$stateParams', 'Wait',
    '$scope', '$rootScope', 'CreateSelect2', 'ParseTypeChange', 'GetBasePath',
    'Rest', 'ParentObject', 'JobTemplateModel', '$q', 'Empty', 'SchedulePost',
    'ProcessErrors', 'SchedulerInit', '$location', 'PromptService',
    function($filter, $state, $stateParams, Wait,
        $scope, $rootScope, CreateSelect2, ParseTypeChange, GetBasePath,
        Rest, ParentObject, JobTemplate, $q, Empty, SchedulePost,
        ProcessErrors, SchedulerInit, $location, PromptService) {

    var base = $scope.base || $location.path().replace(/^\//, '').split('/')[0],
        scheduler,
        job_type;

    var schedule_url = ParentObject.related.schedules || `${ParentObject.related.inventory_source}schedules`;

    let processSchedulerEndDt = function(){
        // set the schedulerEndDt to be equal to schedulerStartDt + 1 day @ midnight
        var dt = new Date($scope.schedulerUTCTime);
        // increment date by 1 day
        dt.setDate(dt.getDate() + 1);
        var month = $filter('schZeroPad')(dt.getMonth() + 1, 2),
            day = $filter('schZeroPad')(dt.getDate(), 2);
        $scope.$parent.schedulerEndDt = month + '/' + day + '/' + dt.getFullYear();
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
    if ($state.current.name === 'jobTemplateSchedules.add'){
        $scope.parseType = 'yaml';
        $scope.extraVars = '---';

        ParseTypeChange({
            scope: $scope,
            variable: 'extraVars',
            parse_variable: 'parseType',
            field_id: 'SchedulerForm-extraVars'
        });

        let jobTemplate = new JobTemplate();

        $q.all([jobTemplate.optionsLaunch(ParentObject.id), jobTemplate.getLaunch(ParentObject.id)])
            .then((responses) => {
                let launchConf = responses[1].data;

                let watchForPromptChanges = () => {
                    let promptValuesToWatch = [
                        'promptData.prompts.inventory.value',
                        'promptData.prompts.verbosity.value',
                        'missingSurveyValue'
                    ];

                    $scope.$watchGroup(promptValuesToWatch, function() {
                        let missingPromptValue = false;
                        if($scope.missingSurveyValue) {
                            missingPromptValue = true;
                        } else if(!$scope.promptData.prompts.inventory.value || !$scope.promptData.prompts.inventory.value.id) {
                            missingPromptValue = true;
                        }
                        $scope.promptModalMissingReqFields = missingPromptValue;
                    });
                };

                if(!launchConf.ask_variables_on_launch) {
                    $scope.noVars = true;
                }

                if(!launchConf.survey_enabled &&
                    !launchConf.ask_inventory_on_launch &&
                    !launchConf.ask_credential_on_launch &&
                    !launchConf.ask_verbosity_on_launch &&
                    !launchConf.ask_job_type_on_launch &&
                    !launchConf.ask_limit_on_launch &&
                    !launchConf.ask_tags_on_launch &&
                    !launchConf.ask_skip_tags_on_launch &&
                    !launchConf.ask_diff_mode_on_launch &&
                    !launchConf.survey_enabled &&
                    !launchConf.credential_needed_to_start &&
                    !launchConf.inventory_needed_to_start &&
                    launchConf.passwords_needed_to_start.length === 0 &&
                    launchConf.variables_needed_to_start.length === 0) {
                        $scope.showPromptButton = false;
                } else {
                    $scope.showPromptButton = true;

                    // Ignore the fact that variables might be promptable on launch
                    // Promptable variables will happen in the schedule form
                    launchConf.ignore_ask_variables = true;

                    if(launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory')) {
                        $scope.promptModalMissingReqFields = true;
                    }

                    if(launchConf.survey_enabled) {
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
    else if ($state.current.name === 'workflowJobTemplateSchedules.add'){
        $scope.parseType = 'yaml';
        // grab any existing extra_vars from parent workflow_job_template
        let defaultUrl = GetBasePath('workflow_job_templates') + $stateParams.id + '/';
        Rest.setUrl(defaultUrl);
        Rest.get().then(function(res){
            var data = res.data.extra_vars;
            $scope.extraVars = data === '' ? '---' :  data;
            ParseTypeChange({
                scope: $scope,
                variable: 'extraVars',
                parse_variable: 'parseType',
                field_id: 'SchedulerForm-extraVars'
            });
        });
    }
    else if ($state.current.name === 'projectSchedules.add'){
        $scope.noVars = true;
    }
    else if ($state.current.name === 'inventories.edit.inventory_sources.edit.schedules.add'){
        $scope.noVars = true;
    }

    job_type = $scope.parentObject.job_type;
    if (!Empty($stateParams.id) && base !== 'system_job_templates' && base !== 'inventories' && !schedule_url) {
        schedule_url = GetBasePath(base) + $stateParams.id + '/schedules/';
    }
    else if(base === "inventories"){
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
    }
    else if (base === 'system_job_templates') {
        schedule_url = GetBasePath(base) + $stateParams.id + '/schedules/';
        if(job_type === "cleanup_facts"){
            $scope.isFactCleanup = true;
            $scope.keep_unit_choices = [{
                "label" : "Days",
                "value" : "d"
            },
            {
                "label": "Weeks",
                "value" : "w"
            },
            {
                "label" : "Years",
                "value" : "y"
            }];
            $scope.granularity_keep_unit_choices =  [{
                "label" : "Days",
                "value" : "d"
            },
            {
                "label": "Weeks",
                "value" : "w"
            },
            {
                "label" : "Years",
                "value" : "y"
            }];
            $scope.prompt_for_days_facts_form.keep_amount.$setViewValue(30);
            $scope.prompt_for_days_facts_form.granularity_keep_amount.$setViewValue(1);
            $scope.keep_unit = $scope.keep_unit_choices[0];
            $scope.granularity_keep_unit = $scope.granularity_keep_unit_choices[1];
        }
        else {
            $scope.cleanupJob = true;
        }
    }

    Wait('start');
    $('#form-container').empty();
    scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false });
    if($scope.schedulerUTCTime) {
        // The UTC time is already set
        processSchedulerEndDt();
    }
    else {
        // We need to wait for it to be set by angular-scheduler because the following function depends
        // on it
        var schedulerUTCTimeWatcher = $scope.$watch('schedulerUTCTime', function(newVal) {
            if(newVal) {
                // Remove the watcher
                schedulerUTCTimeWatcher();
                processSchedulerEndDt();
            }
        });
    }
    scheduler.inject('form-container', false);
    scheduler.injectDetail('occurrences', false);
    scheduler.clear();
    $scope.$on("htmlDetailReady", function() {
        $scope.hideForm = false;
        $scope.$on("formUpdated", function() {
            $rootScope.$broadcast("loadSchedulerDetailPane");
        });

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
            $scope.$emit("formUpdated");
        }, true);

        $scope.$watch("weekDays", function() {
            $scope.$emit("formUpdated");
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

    CreateSelect2({
        element: '.MakeSelect2',
        multiple: false
    });
}];
