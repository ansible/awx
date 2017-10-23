export default
    function ToggleSchedule(Wait, GetBasePath, ProcessErrors, Rest, $state) {
        return function(params) {
            var scope = params.scope,
                id = params.id,
                url = GetBasePath('schedules') + id +'/';

            // Perform the update
            if (scope.removeScheduleFound) {
                scope.removeScheduleFound();
            }
            scope.removeScheduleFound = scope.$on('ScheduleFound', function(e, data) {
                data.enabled = (data.enabled) ? false : true;
                Rest.put(data)
                    .then(() => {
                        Wait('stop');
                        $state.go('.', null, {reload: true});
                    })
                    .catch(({data, status}) => {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to update schedule ' + id + ' PUT returned: ' + status });
                    });
            });

            Wait('start');

            // Get the schedule
            Rest.setUrl(url);
            Rest.get()
                .then(({data}) => {
                    scope.$emit('ScheduleFound', data);
                })
                .catch(({data, status}) => {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve schedule ' + id + ' GET returned: ' + status });
                });
        };
    }

ToggleSchedule.$inject =
    [   'Wait',
        'GetBasePath',
        'ProcessErrors',
        'Rest',
        '$state'
    ];
