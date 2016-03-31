/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function manageHostsDirectiveController($rootScope, $location, $log, $stateParams, $state, $scope, Rest, Alert, HostForm,
    GenerateForm, Prompt, ProcessErrors, GetBasePath, HostsReload, ParseTypeChange, Wait,
    Find, SetStatus, ApplyEllipsis, ToJSON, ParseVariableString, CreateDialog, TextareaResize, ParamPass) {

    var vm = this;

    var params = ParamPass.get();
    if(params === undefined) {
        params = {};
        params.host_scope = $scope.$new();
        params.group_scope = $scope.$new();
    }
    var parent_scope = params.host_scope,
        group_scope = params.group_scope,
        inventory_id = $stateParams.inventory_id,
        mode = $state.current.data.mode, // 'add' or 'edit'
        selected_group_id = params.selected_group_id,
        generator = GenerateForm,
        form = HostForm,
        defaultUrl,
        scope = parent_scope.$new(),
        master = {},
        relatedSets = {},
        url, form_scope;

        var host_id = $stateParams.host_id || undefined;

    form_scope =
        generator.inject(HostForm, {
            mode: 'edit',
            id: 'host-panel-form',
            related: false,
            scope: scope,
            cancelButton: false
        });
    generator.reset();

    // Retrieve detail record and prepopulate the form
    if (mode === 'edit') {
        defaultUrl = GetBasePath('hosts') + host_id + '/';
        Rest.setUrl(defaultUrl);
        Rest.get()
            .success(function(data) {
                var set, fld, related;
                for (fld in form.fields) {
                    if (data[fld]) {
                        scope[fld] = data[fld];
                        master[fld] = scope[fld];
                    }
                }
                related = data.related;
                for (set in form.related) {
                    if (related[set]) {
                        relatedSets[set] = {
                            url: related[set],
                            iterator: form.related[set].iterator
                        };
                    }
                }
                scope.variable_url = data.related.variable_data;
                scope.has_inventory_sources = data.has_inventory_sources;
                scope.parseType = 'yaml';
                ParseTypeChange({
                    scope: scope,
                    field_id: 'host_variables',
                });

            })
            .error(function(data, status) {
                ProcessErrors(parent_scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to retrieve host: ' + host_id + '. GET returned status: ' + status
                });
            });
    } else {
        if (selected_group_id) {
            // adding hosts to a group
            url = GetBasePath('groups') + selected_group_id + '/';
        } else {
            // adding hosts to the top-level (inventory)
            url = GetBasePath('inventory') + inventory_id + '/';
        }
        // Add mode
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                scope.has_inventory_sources = data.has_inventory_sources;
                scope.enabled = true;
                scope.variables = '---';
                defaultUrl = data.related.hosts;
                //scope.$emit('hostVariablesLoaded');
                scope.parseType = 'yaml';
                ParseTypeChange({
                    scope: scope,
                    field_id: 'host_variables',
                });

            })
            .error(function(data, status) {
                ProcessErrors(parent_scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to retrieve group: ' + selected_group_id + '. GET returned status: ' + status
                });
            });
    }

    if (scope.removeSaveCompleted) {
        scope.removeSaveCompleted();
    }
    scope.removeSaveCompleted = scope.$on('saveCompleted', function() {
        Wait('stop');
        try {
            $('#host-modal-dialog').dialog('close');
        } catch (err) {
            // ignore
        }
        if (group_scope && group_scope.refreshHosts) {
            group_scope.refreshHosts();
        }
        if (parent_scope.refreshHosts) {
            parent_scope.refreshHosts();
        }
        scope.$destroy();
        $state.go('inventoryManage', {}, {
            reload: true
        });
    });

    // Save changes to the parent
    var saveHost = function() {
        Wait('start');
        var fld, data = {};

        try {
            data.variables = ToJSON(scope.parseType, scope.variables, true);
            for (fld in form.fields) {
                data[fld] = scope[fld];
            }
            data.inventory = inventory_id;
            Rest.setUrl(defaultUrl);
            if (mode === 'edit') {
                Rest.put(data)
                    .success(function() {
                        scope.$emit('saveCompleted');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, form, {
                            hdr: 'Error!',
                            msg: 'Failed to update host: ' + host_id + '. PUT returned status: ' + status
                        });
                    });
            } else {
                Rest.post(data)
                    .success(function() {
                        scope.$emit('saveCompleted');
                    })
                    .error(function(data, status) {
                        ProcessErrors(scope, data, status, form, {
                            hdr: 'Error!',
                            msg: 'Failed to create host. POST returned status: ' + status
                        });
                    });
            }
        } catch (e) {
            // ignore. ToJSON will have already alerted the user
        }
    };

    var cancelPanel = function() {
        scope.$destroy();
        if (scope.codeMirror) {
            scope.codeMirror.destroy();
        }
        $state.go('inventoryManage');
    };

    angular.extend(vm, {
        cancelPanel: cancelPanel,
        saveHost: saveHost,
				mode: mode
    });
}

export default ['$rootScope', '$location', '$log', '$stateParams', '$state', '$scope', 'Rest', 'Alert', 'HostForm',
    'GenerateForm', 'Prompt', 'ProcessErrors', 'GetBasePath', 'HostsReload', 'ParseTypeChange',
    'Wait', 'Find', 'SetStatus', 'ApplyEllipsis', 'ToJSON', 'ParseVariableString',
    'CreateDialog', 'TextareaResize', 'ParamPass', manageHostsDirectiveController
];
