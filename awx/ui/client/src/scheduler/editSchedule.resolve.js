function editScheduleResolve () {
    const resolve = {
        scheduleResolve: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors',
            (Rest, $stateParams, GetBasePath, ProcessErrors) => {
                var path = `${GetBasePath('schedules')}${parseInt($stateParams.schedule_id)}/`;
                Rest.setUrl(path);
                return Rest.get()
                    .then(function(data) {
                        return (data.data);
                    }).catch(function(response) {
                        ProcessErrors(null, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get schedule info. GET returned status: ' +
                                response.status
                        });
                    });
            }
        ],
        timezonesResolve: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors',
            (Rest, $stateParams, GetBasePath, ProcessErrors) => {
                var path = `${GetBasePath('schedules')}zoneinfo`;
                Rest.setUrl(path);
                return Rest.get()
                    .then(function(data) {
                        return (data.data);
                    }).catch(function(response) {
                        ProcessErrors(null, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get zoneinfo. GET returned status: ' +
                                response.status
                        });
                    });
            }
        ]
    };
    return resolve;
}
export default editScheduleResolve;
