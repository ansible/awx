export default ['$filter', '$state', '$stateParams', 'Wait', '$scope',
'$rootScope', '$http', 'CreateSelect2', 'ParseTypeChange', 'ParentObject', 'ProcessErrors', 'Rest',
'GetBasePath', 'SchedulerInit', 'SchedulePost', 'JobTemplateModel', '$q', 'Empty', 'PromptService', 'RRuleToAPI',
function($filter, $state, $stateParams, Wait, $scope,
    $rootScope, $http, CreateSelect2, ParseTypeChange, ParentObject, ProcessErrors, Rest,
    GetBasePath, SchedulerInit, SchedulePost, JobTemplate, $q, Empty, PromptService, RRuleToAPI) {

    let schedule, scheduler;

    // initial end @ midnight values
    $scope.schedulerEndHour = "00";
    $scope.schedulerEndMinute = "00";
    $scope.schedulerEndSecond = "00";
    $scope.parentObject = ParentObject;
    $scope.isEdit = true;
    $scope.hideForm = true;
    $scope.parseType = 'yaml';

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
            promptData: $scope.promptData
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
    };

    $scope.$on("updateSchedulerSelects", function() {
        callSelect2();
    });

    $scope.$on("setPreviewPane", (event) => {
        let rrule = event.currentScope.rrule.toString();
        let req = RRuleToAPI(rrule, $scope);

        $http.post('/api/v2/schedules/preview/', {'rrule': req})
            .then(({data}) => {
                $scope.preview_list = data;
                for (let tz in data) {
                    $scope.preview_list.isEmpty = data[tz].length === 0;
                    $scope.preview_list[tz] = data[tz].map(function(date) {
                        return date.replace(/Z/, '');
                    });
                }
            });
    });

    Wait('start');

    // Get the existing record
    Rest.setUrl(GetBasePath('schedules') + parseInt($stateParams.schedule_id) + '/');
    Rest.get()
        .then(({data}) => {
            schedule = data;
            try {
                schedule.extra_data = JSON.parse(schedule.extra_data);
            } catch(e) {
                // do nothing
            }

            $scope.extraVars = (data.extra_data === '' || _.isEmpty(data.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(data.extra_data);

            if(schedule.extra_data.hasOwnProperty('granularity')){
                $scope.isFactCleanup = true;
            }
            if (schedule.extra_data.hasOwnProperty('days')){
                $scope.cleanupJob = true;
            }

            $scope.schedule_obj = data;

            $('#form-container').empty();
            scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false });

            $http.get('/api/v2/schedules/zoneinfo/').then(({data}) => {
                scheduler.scope.timeZones = data;
                scheduler.scope.schedulerTimeZone = _.find(data, (zone) => {
                    return zone.name === scheduler.scope.current_timezone.name;
                });
            });
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
                    "schedulerEndDt"
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

            if($scope.isFactCleanup || $scope.cleanupJob){
                var a,b, prompt_for_days,
                    keep_unit,
                    granularity,
                    granularity_keep_unit;

                if($scope.cleanupJob){
                    $scope.schedulerPurgeDays = Number(schedule.extra_data.days);
                }
                else if($scope.isFactCleanup){
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
                    // the API returns something like 20w or 1y
                    a = schedule.extra_data.older_than; // "20y"
                    b = schedule.extra_data.granularity; // "1w"
                    prompt_for_days = Number(_.initial(a,1).join('')); // 20
                    keep_unit = _.last(a); // "y"
                    granularity = Number(_.initial(b,1).join('')); // 1
                    granularity_keep_unit = _.last(b); // "w"

                    $scope.keep_amount = prompt_for_days;
                    $scope.granularity_keep_amount = granularity;
                    $scope.keep_unit = _.find($scope.keep_unit_choices, function(i){
                        return i.value === keep_unit;
                    });
                    $scope.granularity_keep_unit =_.find($scope.granularity_keep_unit_choices, function(i){
                        return i.value === granularity_keep_unit;
                    });
                }
            }

            if ($state.current.name === 'jobTemplateSchedules.edit'){

                let jobTemplate = new JobTemplate();

                Rest.setUrl(data.related.credentials);

                $q.all([jobTemplate.optionsLaunch(ParentObject.id), jobTemplate.getLaunch(ParentObject.id), Rest.get()])
                    .then((responses) => {
                        let launchOptions = responses[0].data,
                            launchConf = responses[1].data,
                            scheduleCredentials = responses[2].data;


                        let watchForPromptChanges = () => {
                            let promptValuesToWatch = [
                                // credential passwords...?
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

                        let prompts = PromptService.processPromptValues({
                            launchConf: responses[1].data,
                            launchOptions: responses[0].data,
                            currentValues: data
                        });

                        prompts.credentials.value = scheduleCredentials.results.length > 0 ? scheduleCredentials.results : prompts.credentials.value;

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

                            if(launchConf.ask_inventory_on_launch && !_.has(launchConf, 'defaults.inventory') && !_.has(data, 'summary_fields.inventory')) {
                                $scope.promptModalMissingReqFields = true;
                            }

                            if(responses[1].data.survey_enabled) {
                                // go out and get the survey questions
                                jobTemplate.getSurveyQuestions(ParentObject.id)
                                    .then((surveyQuestionRes) => {

                                        let processed = PromptService.processSurveyQuestions({
                                            surveyQuestions: surveyQuestionRes.data.spec,
                                            extra_data: data.extra_data
                                        });

                                        $scope.missingSurveyValue = processed.missingSurveyValue;

                                        $scope.extraVars = (processed.extra_data === '' || _.isEmpty(processed.extra_data)) ? '---' : '---\n' + jsyaml.safeDump(processed.extra_data);

                                        ParseTypeChange({
                                            scope: $scope,
                                            variable: 'extraVars',
                                            parse_variable: 'parseType',
                                            field_id: 'SchedulerForm-extraVars',
                                            readOnly: !$scope.schedule_obj.summary_fields.user_capabilities.edit
                                        });

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
                                    template: ParentObject.id
                                };
                                watchForPromptChanges();
                            }
                        }
                    });
            }

            // extra_data field is not manifested in the UI when scheduling a Management Job
            if ($state.current.name !== 'managementJobsList.schedule.add' && $state.current.name !== 'managementJobsList.schedule.edit'){
                if ($state.current.name === 'projectSchedules.edit'){
                    $scope.noVars = true;
                }
                else if ($state.current.name === 'inventories.edit.inventory_sources.edit.schedules.edit'){
                    $scope.noVars = true;
                }
                else {
                    ParseTypeChange({
                        scope: $scope,
                        variable: 'extraVars',
                        parse_variable: 'parseType',
                        field_id: 'SchedulerForm-extraVars',
                        readOnly: !$scope.schedule_obj.summary_fields.user_capabilities.edit
                    });
                }
            }
        })
        .catch(({data, status}) => {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to retrieve schedule ' + parseInt($stateParams.schedule_id) + ' GET returned: ' + status });
        });

    callSelect2();
}];
