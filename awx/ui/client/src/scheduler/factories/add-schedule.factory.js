export default
    function AddSchedule($location, $rootScope, $stateParams, SchedulerInit,
        Wait, GetBasePath, Empty, SchedulePost, $state, Rest,
        ProcessErrors) {
        return function(params) {
            var scope = params.scope,
                callback= params.callback,
                base = params.base || $location.path().replace(/^\//, '').split('/')[0],
                url = params.url || null,
                scheduler,
                job_type;

            job_type = scope.parentObject.job_type;
            if (!Empty($stateParams.id) && base !== 'system_job_templates' && base !== 'inventories' && !url) {
                url = GetBasePath(base) + $stateParams.id + '/schedules/';
            }
            else if(base === "inventories"){
                if (!params.url){
                    url = GetBasePath('groups') + $stateParams.id + '/';
                    Rest.setUrl(url);
                    Rest.get().
                    then(function (data) {
                            url = data.data.related.inventory_source + 'schedules/';
                        }).catch(function (response) {
                        ProcessErrors(null, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get inventory group info. GET returned status: ' +
                            response.status
                        });
                    });
                }
                else {
                    url = params.url;
                }
            }
            else if (base === 'system_job_templates') {
                url = GetBasePath(base) + $stateParams.id + '/schedules/';
                if(job_type === "cleanup_facts"){
                    scope.isFactCleanup = true;
                    scope.keep_unit_choices = [{
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
                    scope.granularity_keep_unit_choices =  [{
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
                    scope.prompt_for_days_facts_form.keep_amount.$setViewValue(30);
                    scope.prompt_for_days_facts_form.granularity_keep_amount.$setViewValue(1);
                    scope.keep_unit = scope.keep_unit_choices[0];
                    scope.granularity_keep_unit = scope.granularity_keep_unit_choices[1];
                }
                else {
                    scope.cleanupJob = true;
                }
            }

            Wait('start');
            $('#form-container').empty();
            scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
            if(scope.schedulerUTCTime) {
                // The UTC time is already set
                scope.processSchedulerEndDt();
            }
            else {
                // We need to wait for it to be set by angular-scheduler because the following function depends
                // on it
                var schedulerUTCTimeWatcher = scope.$watch('schedulerUTCTime', function(newVal) {
                    if(newVal) {
                        // Remove the watcher
                        schedulerUTCTimeWatcher();
                        scope.processSchedulerEndDt();
                    }
                });
            }
            scheduler.inject('form-container', false);
            scheduler.injectDetail('occurrences', false);
            scheduler.clear();
            scope.$on("htmlDetailReady", function() {
                $rootScope.$broadcast("ScheduleFormCreated", scope);
            });
            scope.showRRuleDetail = false;

            if (scope.removeScheduleSaved) {
                scope.removeScheduleSaved();
            }
            scope.removeScheduleSaved = scope.$on('ScheduleSaved', function(e, data) {
                Wait('stop');
                if (callback) {
                    scope.$emit(callback, data);
                }
                $state.go("^", null, {reload: true});
            });
            scope.saveSchedule = function() {
                SchedulePost({
                    scope: scope,
                    url: url,
                    scheduler: scheduler,
                    callback: 'ScheduleSaved',
                    mode: 'add'
                });
            };

            $('#scheduler-tabs li a').on('shown.bs.tab', function(e) {
                if ($(e.target).text() === 'Details') {
                    if (!scheduler.isValid()) {
                        $('#scheduler-tabs a:first').tab('show');
                    }
                }
            });
        };
    }

AddSchedule.$inject =
    [   '$location', '$rootScope', '$stateParams',
        'SchedulerInit', 'Wait', 'GetBasePath',
        'Empty', 'SchedulePost', '$state',
        'Rest', 'ProcessErrors'
    ];
