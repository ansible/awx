export default
    function EditSchedule(SchedulerInit, $rootScope, Wait, Rest, ProcessErrors,
        GetBasePath, SchedulePost, $state) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                callback = params.callback,
                schedule, scheduler,
                url = GetBasePath('schedules') + id + '/';

            delete scope.isFactCleanup;
            delete scope.cleanupJob;

            function setGranularity(){
                var a,b, prompt_for_days,
                    keep_unit,
                    granularity,
                    granularity_keep_unit;

                if(scope.cleanupJob){
                    scope.schedulerPurgeDays = Number(schedule.extra_data.days);
                    // scope.scheduler_form.schedulerPurgeDays.$setViewValue( Number(schedule.extra_data.days));
                }
                else if(scope.isFactCleanup){
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
                    // the API returns something like 20w or 1y
                    a = schedule.extra_data.older_than; // "20y"
                    b = schedule.extra_data.granularity; // "1w"
                    prompt_for_days = Number(_.initial(a,1).join('')); // 20
                    keep_unit = _.last(a); // "y"
                    granularity = Number(_.initial(b,1).join('')); // 1
                    granularity_keep_unit = _.last(b); // "w"

                    scope.keep_amount = prompt_for_days;
                    scope.granularity_keep_amount = granularity;
                    scope.keep_unit = _.find(scope.keep_unit_choices, function(i){
                        return i.value === keep_unit;
                    });
                    scope.granularity_keep_unit =_.find(scope.granularity_keep_unit_choices, function(i){
                        return i.value === granularity_keep_unit;
                    });
                }
            }

            if (scope.removeScheduleFound) {
                scope.removeScheduleFound();
            }
            scope.removeScheduleFound = scope.$on('ScheduleFound', function() {
                $('#form-container').empty();
                scheduler = SchedulerInit({ scope: scope, requireFutureStartTime: false });
                scheduler.inject('form-container', false);
                scheduler.injectDetail('occurrences', false);

                if (!/DTSTART/.test(schedule.rrule)) {
                    schedule.rrule += ";DTSTART=" + schedule.dtstart.replace(/\.\d+Z$/,'Z');
                }
                schedule.rrule = schedule.rrule.replace(/ RRULE:/,';');
                schedule.rrule = schedule.rrule.replace(/DTSTART:/,'DTSTART=');
                scope.$on("htmlDetailReady", function() {
                    scheduler.setRRule(schedule.rrule);
                    scheduler.setName(schedule.name);
                    $rootScope.$broadcast("ScheduleFormCreated", scope);
                });
                scope.showRRuleDetail = false;

                scheduler.setRRule(schedule.rrule);
                scheduler.setName(schedule.name);
                if(scope.isFactCleanup || scope.cleanupJob){
                    setGranularity();
                }
            });


            if (scope.removeScheduleSaved) {
                scope.removeScheduleSaved();
            }
            scope.removeScheduleSaved = scope.$on('ScheduleSaved', function(e, data) {
                Wait('stop');
                if (callback) {
                    scope.$emit(callback, data);
                }
                $state.go("^");
            });
            scope.saveSchedule = function() {
                schedule.extra_data = scope.extraVars;
                SchedulePost({
                    scope: scope,
                    url: url,
                    scheduler: scheduler,
                    callback: 'ScheduleSaved',
                    mode: 'edit',
                    schedule: schedule
                });
            };

            Wait('start');

            // Get the existing record
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    schedule = data;
                    try {
                        schedule.extra_data = JSON.parse(schedule.extra_data);
                    } catch(e) {
                        // do nothing
                    }
                    scope.extraVars = data.extra_data === '' ? '---' : '---\n' + jsyaml.safeDump(data.extra_data);

                    if(schedule.extra_data.hasOwnProperty('granularity')){
                        scope.isFactCleanup = true;
                    }
                    if (schedule.extra_data.hasOwnProperty('days')){
                        scope.cleanupJob = true;
                    }

                    scope.schedule_obj = data;

                    scope.$emit('ScheduleFound');
                })
                .error(function(data,status){
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve schedule ' + id + ' GET returned: ' + status });
                });
        };
    }

EditSchedule.$inject =
    [   'SchedulerInit', '$rootScope', 'Wait', 'Rest',
        'ProcessErrors', 'GetBasePath', 'SchedulePost', '$state'
    ];
