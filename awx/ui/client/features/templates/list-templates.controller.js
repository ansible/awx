function ListTemplatesController (model, strings, $state, $scope, rbacUiControlService, Dataset, $filter, Alert, InitiatePlaybookRun, Prompt, Wait, ProcessErrors) {
    const vm = this || {}
    const unifiedJobTemplate = model;

    init();

    function init() {
        vm.strings = strings;

        // TODO: add the permission based functionality to the base model
        $scope.canAdd = false;
        rbacUiControlService.canAdd("job_templates")
            .then(function(params) {
                $scope.canAddJobTemplate = params.canAdd;
            });
        rbacUiControlService.canAdd("workflow_job_templates")
            .then(function(params) {
                $scope.canAddWorkflowJobTemplate = params.canAdd;
            });
        $scope.$watchGroup(["canAddJobTemplate", "canAddWorkflowJobTemplate"], function() {
            if ($scope.canAddJobTemplate || $scope.canAddWorkflowJobTemplate) {
                $scope.canAdd = true;
            } else {
                $scope.canAdd = false;
            }
        });

        $scope.list = {
            iterator: 'template',
            name: 'templates'
        };
        $scope.collection = {
            basePath: 'unified_job_templates',
            iterator: 'template'
        };
        $scope[`${$scope.list.iterator}_dataset`] = Dataset.data;
        $scope[$scope.list.name] = $scope[`${$scope.list.iterator}_dataset`].results;
        $scope.$on('updateDataset', function(e, dataset) {
            $scope[`${$scope.list.iterator}_dataset`] = dataset;
            $scope[$scope.list.name] = dataset.results;
        });
    }

    // get modified date and user who modified it
    vm.getModified = function(template) {
        let val = "";
        if (template.modified) {
            val += $filter('longDate')(template.modified);
        }
        if (_.has(template, 'summary_fields.modified_by.username')) {
                val += ` by <a href="/#/users/${template.summary_fields.modified_by.id}">${template.summary_fields.modified_by.username}</a>`;
        }
        if (val === "") {
            val = undefined;
        }
        return val;
    };

    // get last ran date and user who ran it
    vm.getRan = function(template) {
        let val = "";
        if (template.last_job_run) {
            val += $filter('longDate')(template.last_job_run);
        }

        // TODO: when API gives back a user who last ran the job in summary fields, uncomment and
        // update this code
        // if (template && template.summary_fields && template.summary_fields.modified_by &&
        //     template.summary_fields.modified_by.username) {
        //         val += ` by <a href="/#/users/${template.summary_fields.modified_by.id}">${template.summary_fields.modified_by.username}</a>`;
        // }

        if (val === "") {
            val = undefined;
        }
        return val;
    };

    // get pretified template type names from options
    vm.templateTypes = unifiedJobTemplate.options('actions.GET.type.choices')
        .reduce((acc, i) => {
            acc[i[0]] = i[1];
            return acc;
        }, {});

    // get if you should show the active indicator for the row or not
    // TODO: edit indicator doesn't update when you enter edit route after initial load right now
    vm.activeId = parseInt($state.params.job_template_id || $state.params.workflow_template_id);

    // TODO: update to new way of launching job after mike opens his pr
    vm.submitJob = function(template) {
        if(template) {
            if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                InitiatePlaybookRun({ scope: $scope, id: template.id, job_type: 'job_template' });
            }
            else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                InitiatePlaybookRun({ scope: $scope, id: template.id, job_type: 'workflow_job_template' });
            }
            else {
                var alertStrings = {
                    header: 'Error: Unable to determine template type',
                    body: 'We were unable to determine this template\'s type while launching.'
                }
                Alert(strings.get('ALERT', alertStrings));
            }
        } else {
            var alertStrings = {
                header: 'Error: Unable to launch template',
                body: 'Template parameter is missing'
            }
            Alert(strings.get('ALERT', alertStrings));
        }
    };

    // TODO: implement copy function
    vm.copyTemplate = function(template) {
    };

    vm.deleteTemplate = function(template) {
        var action = function() {
            $('#prompt-modal').modal('hide');
            Wait('start');
            // TODO: The request url doesn't work here
            unifiedJobTemplate.request('delete', template.id)
                .then(() => {

                    let reloadListStateParams = null;

                    if($scope.templates.length === 1 && $state.params.template_search && !_.isEmpty($state.params.template_search.page) && $state.params.template_search.page !== '1') {
                        reloadListStateParams = _.cloneDeep($state.params);
                        reloadListStateParams.template_search.page = (parseInt(reloadListStateParams.template_search.page)-1).toString();
                    }

                    if (parseInt($state.params.template_id) === template.id) {
                        $state.go("^", reloadListStateParams, { reload: true });
                    } else {
                        $state.go('.', reloadListStateParams, {reload: true});
                    }
                })
                .catch(({data, status}) => {
                    ProcessErrors($scope, data, status, null, {
                        hdr: string.get('error.HEADER'),
                        msg: strings.get('error.CALL', {path: "" + unifiedJobTemplate.path + template.id, status})
                    });
                })
                .finally(function() {
                    Wait('stop');
                });
        };

        let deleteModalBody = `<div class="Prompt-bodyQuery">${strings.get('deleteResource.CONFIRM', 'template')}</div>`;

        Prompt({
            hdr: strings.get('deleteResource.HEADER'),
            resourceName: $filter('sanitize')(template.name),
            body: deleteModalBody,
            action: action,
            actionText: 'DELETE'
        });
    };
}

ListTemplatesController.$inject = [
    'resolvedModels',
    'TemplatesStrings',
    '$state',
    '$scope',
    'rbacUiControlService',
    'Dataset',
    '$filter',
    'Alert',
    'InitiatePlaybookRun',
    'Prompt',
    'Wait',
    'ProcessErrors'
];

export default ListTemplatesController;
