export default
    function SchedulePost(Rest, ProcessErrors, RRuleToAPI, Wait) {
        return function(params) {
            var scope = params.scope,
                url = params.url,
                scheduler = params.scheduler,
                mode = params.mode,
                schedule = (params.schedule) ? params.schedule : {},
                callback = params.callback,
                newSchedule, rrule, extra_vars;
            if (scheduler.isValid()) {
                Wait('start');
                newSchedule = scheduler.getValue();
                rrule = scheduler.getRRule();
                schedule.name = newSchedule.name;
                schedule.rrule = RRuleToAPI(rrule.toString());
                schedule.description = (/error/.test(rrule.toText())) ? '' : rrule.toText();

                if (scope.isFactCleanup) {
                    extra_vars = {
                        "older_than": scope.scheduler_form.keep_amount.$viewValue + scope.scheduler_form.keep_unit.$viewValue.value,
                        "granularity": scope.scheduler_form.granularity_keep_amount.$viewValue + scope.scheduler_form.granularity_keep_unit.$viewValue.value
                    };
                    schedule.extra_data = JSON.stringify(extra_vars);
                } else if (scope.cleanupJob) {
                    extra_vars = {
                        "days" : scope.scheduler_form.schedulerPurgeDays.$viewValue
                    };
                    schedule.extra_data = JSON.stringify(extra_vars);
                }
                else if(scope.extraVars){
                    schedule.extra_data = scope.parseType === 'yaml' ?
                        (scope.extraVars === '---' ? "" : jsyaml.safeLoad(scope.extraVars)) : scope.extraVars;
                }
                Rest.setUrl(url);
                if (mode === 'add') {
                    Rest.post(schedule)
                        .success(function(){
                            if (callback) {
                                scope.$emit(callback);
                            }
                            else {
                                Wait('stop');
                            }
                        })
                        .error(function(data, status){
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });
                        });
                }
                else {
                    Rest.put(schedule)
                        .success(function(){
                            if (callback) {
                                scope.$emit(callback, schedule);
                            }
                            else {
                                Wait('stop');
                            }
                        })
                        .error(function(data, status){
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'POST to ' + url + ' returned: ' + status });
                        });
                }
            }
            else {
                return false;
            }
        };
    }

SchedulePost.$inject =
    [   'Rest',
        'ProcessErrors',
        'RRuleToAPI',
        'Wait'
    ];
