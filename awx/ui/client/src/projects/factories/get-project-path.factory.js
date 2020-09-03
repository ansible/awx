export default
    function GetProjectPath(i18n, Rest, GetBasePath, ProcessErrors) {
        return function(params) {
            var scope = params.scope,
                main = params.main;

            function arraySort(data) {
                //Sort nodes by name
                var i, j, names = [],
                    newData = [];
                for (i = 0; i < data.length; i++) {
                    names.push(data[i].value);
                }
                names.sort();
                for (j = 0; j < names.length; j++) {
                    for (i = 0; i < data.length; i++) {
                        if (data[i].value === names[j]) {
                            newData.push(data[i]);
                        }
                    }
                }
                return newData;
            }

            scope.showMissingPlaybooksAlert = false;

            Rest.setUrl(GetBasePath('config'));
            Rest.get()
                .then(({data}) => {
                    var opts = [], i;
                    if (data.project_local_paths) {
                        for (i = 0; i < data.project_local_paths.length; i++) {
                            opts.push({
                                label: data.project_local_paths[i],
                                value: data.project_local_paths[i]
                            });
                        }
                    }
                    if (scope.local_path) {
                        // List only includes paths not assigned to projects, so add the
                        // path assigned to the current project.
                        opts.push({
                            label: scope.local_path,
                            value: scope.local_path
                        });
                    }
                    scope.project_local_paths = arraySort(opts);
                    if (scope.local_path) {
                        for (i = 0; scope.project_local_paths.length; i++) {
                            if (scope.project_local_paths[i].value === scope.local_path) {
                                scope.local_path = scope.project_local_paths[i];
                                break;
                            }
                        }
                    }
                    scope.base_dir = data.project_base_dir || i18n._('You do not have access to view this property');
                    main.local_path = scope.local_path;
                    main.base_dir = scope.base_dir; // Keep in main object so that it doesn't get
                    // wiped out on form reset.
                    if (opts.length === 0) {
                        // trigger display of alert block when scm_type == manual
                        scope.showMissingPlaybooksAlert = true;
                    }
                    scope.$emit('pathsReady');
                })
                .catch(({data, status}) => {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: i18n._('Failed to access API config. GET status: ') + status });
                });
        };
    }

GetProjectPath.$inject =
    [   'i18n',
        'Rest',
        'GetBasePath',
        'ProcessErrors'
    ];
