/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
 */

function InventoriesEdit($scope, $rootScope, $compile, $location,
    $log, $stateParams, InventoryForm, Rest, Alert, ProcessErrors,
    ClearScope, GetBasePath, ParseTypeChange, Wait, ToJSON,
    ParseVariableString, Prompt, InitiatePlaybookRun,
    TemplatesService, $state, $filter) {

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm(),
        inventory_id = $stateParams.inventory_id,
        master = {},
        fld, json_data, data;

    ClearScope();
    init();

    function init() {
        ClearScope();
        form.formLabelSize = null;
        form.formFieldSize = null;
        $scope.inventory_id = inventory_id;

        $scope.$watch('invnentory_obj.summary_fields.user_capabilities.edit', function(val) {
            if (val === false) {
                $scope.canAdd = false;
            }
        });
    }


    Wait('start');
    Rest.setUrl(GetBasePath('inventory') + inventory_id + '/');
    Rest.get()
        .success(function(data) {
            var fld;
            for (fld in form.fields) {
                if (fld === 'variables') {
                    $scope.variables = ParseVariableString(data.variables);
                    master.variables = $scope.variables;
                } else if (fld === 'inventory_name') {
                    $scope[fld] = data.name;
                    master[fld] = $scope[fld];
                } else if (fld === 'inventory_description') {
                    $scope[fld] = data.description;
                    master[fld] = $scope[fld];
                } else if (data[fld]) {
                    $scope[fld] = data[fld];
                    master[fld] = $scope[fld];
                }
                if (form.fields[fld].sourceModel && data.summary_fields &&
                    data.summary_fields[form.fields[fld].sourceModel]) {
                    $scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                    master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                        data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                }
            }

            Wait('stop');
            $scope.parseType = 'yaml';
            ParseTypeChange({
                scope: $scope,
                variable: 'variables',
                parse_variable: 'parseType',
                field_id: 'inventory_variables'
            });

            $scope.inventory_obj = data;

            $scope.$emit('inventoryLoaded');
        })
        .error(function(data, status) {
            ProcessErrors($scope, data, status, null, {
                hdr: 'Error!',
                msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status
            });
        });
    // Save
    $scope.formSave = function() {
        Wait('start');

        // Make sure we have valid variable data
        json_data = ToJSON($scope.parseType, $scope.variables);

        data = {};
        for (fld in form.fields) {
            if (form.fields[fld].realName) {
                data[form.fields[fld].realName] = $scope[fld];
            } else {
                data[fld] = $scope[fld];
            }
        }

        Rest.setUrl(defaultUrl + inventory_id + '/');
        Rest.put(data)
            .success(function() {
                Wait('stop');
                $state.go($state.current, {}, { reload: true });
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to update inventory. PUT returned status: ' + status
                });
            });
    };

    $scope.manageInventory = function() {
        $location.path($location.path() + '/manage');
    };

    $scope.formCancel = function() {
        $state.go('inventories');
    };

    $scope.addScanJob = function() {
        $location.path($location.path() + '/job_templates/add');
    };

    $scope.launchScanJob = function() {
        InitiatePlaybookRun({ scope: $scope, id: this.scan_job_template.id });
    };

    $scope.scheduleScanJob = function() {
        $location.path('/job_templates/' + this.scan_job_template.id + '/schedules');
    };

    $scope.editScanJob = function() {
        $location.path($location.path() + '/job_templates/' + this.scan_job_template.id);
    };

    $scope.deleteScanJob = function () {
        var id = this.scan_job_template.id ,
          action = function () {
            $('#prompt-modal').modal('hide');
            Wait('start');
            TemplatesService.deleteJobTemplate(id)
                .success(function () {
                  $('#prompt-modal').modal('hide');
                  // @issue: OLD SEARCH
                  // $scope.search(form.related.scan_job_templates.iterator);
                })
                .error(function (data) {
                    Wait('stop');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'DELETE returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the job template below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(this.scan_job_template.name) + '</div>',
            action: action,
            actionText: 'DELETE'
        });

    };

}

export default ['$scope', '$rootScope', '$compile', '$location',
    '$log', '$stateParams', 'InventoryForm', 'Rest', 'Alert',
    'ProcessErrors', 'ClearScope', 'GetBasePath', 'ParseTypeChange', 'Wait',
    'ToJSON', 'ParseVariableString', 'Prompt', 'InitiatePlaybookRun',
    'TemplatesService', '$state', '$filter', InventoriesEdit,
];
