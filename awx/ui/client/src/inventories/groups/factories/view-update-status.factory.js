export default
    function ViewUpdateStatus($state, Rest, ProcessErrors, Alert, Wait, Empty, Find) {
        return function(params) {
            var scope = params.scope,
            group_id = params.group_id,
            group = Find({ list: scope.groups, key: 'id', val: group_id });

            if (scope.removeSourceReady) {
                scope.removeSourceReady();
            }
            scope.removeSourceReady = scope.$on('SourceReady', function(e, source) {

               // Get the ID from the correct summary field
               var update_id = (source.summary_fields.current_update) ? source.summary_fields.current_update.id : source.summary_fields.last_update.id;

               $state.go('inventorySyncStdout', {id: update_id});

            });

            if (group) {
                if (Empty(group.source)) {
                    // do nothing
                } else if (Empty(group.status) || group.status === "never updated") {
                    Alert('No Status Available', '<div>An inventory sync has not been performed for the selected group. Start the process by ' +
                          'clicking the <i class="fa fa-refresh"></i> button.</div>', 'alert-info', null, null, null, null, true);
                } else {
                    Wait('start');
                    Rest.setUrl(group.related.inventory_source);
                    Rest.get()
                    .success(function (data) {
                        scope.$emit('SourceReady', data);
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                      msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source +
                                          ' GET returned status: ' + status });
                    });
                }
            }
        };
    }

ViewUpdateStatus.$inject =
    [   '$state', 'Rest', 'ProcessErrors',
        'Alert', 'Wait', 'Empty', 'Find'
    ];
