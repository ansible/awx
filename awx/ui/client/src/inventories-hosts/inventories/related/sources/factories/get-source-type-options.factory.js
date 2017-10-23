export default
    function GetSourceTypeOptions(Rest, ProcessErrors, GetBasePath) {
        return function(params) {
            var scope = params.scope,
            variable = params.variable;

            if (scope[variable] === undefined) {
                scope[variable] = [];
                Rest.setUrl(GetBasePath('inventory_sources'));
                Rest.options()
                .then(({data}) => {
                    var i, choices = data.actions.GET.source.choices;
                    for (i = 0; i < choices.length; i++) {
                        if (choices[i][0] !== 'file' && choices[i][0] !== "") {
                            scope[variable].push({
                                label: choices[i][1],
                                value: choices[i][0]
                            });
                        }
                    }
                    scope.cloudCredentialRequired = false;
                    scope.$emit('sourceTypeOptionsReady');
                })
                .catch(({data, status}) => {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                  msg: 'Failed to retrieve options for inventory_sources.source. OPTIONS status: ' + status
                    });
                });
            }
        };
    }

GetSourceTypeOptions.$inject =
    [   'Rest',
        'ProcessErrors',
        'GetBasePath'
    ];
