/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  JobTemplates.js
 *
 *  Controller functions for the Job Template model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:JobTemplate
 * @description This controller's for the Job Template page
*/


export function JobTemplatesList($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobTemplateList,
    GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors,
    GetBasePath, JobTemplateForm, CredentialList, LookUpInit, PlaybookRun, Wait, Stream, CreateDialog, $compile) {

    ClearScope();

    var list = JobTemplateList,
        defaultUrl = GetBasePath('job_templates'),
        view = GenerateList,
        base = $location.path().replace(/^\//, '').split('/')[0],
        mode = (base === 'job_templates') ? 'edit' : 'select';

    view.inject(list, { mode: mode, scope: $scope });
    $rootScope.flashMessage = null;

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        // Cleanup after a delete
        Wait('stop');
        $('#prompt-modal').modal('hide');
    });

    SearchInit({
        scope: $scope,
        set: 'job_templates',
        list: list,
        url: defaultUrl
    });
    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl
    });

    // Called from Inventories tab, host failed events link:
    if ($routeParams.name) {
        $scope[list.iterator + 'SearchField'] = 'name';
        $scope[list.iterator + 'SearchValue'] = $routeParams.name;
        $scope[list.iterator + 'SearchFieldLabel'] = list.fields.name.label;
    }

    $scope.search(list.iterator);

    LoadBreadCrumbs();



    $scope.showActivity = function () {
        Stream({ scope: $scope });
    };

    $scope.addJobTemplate = function () {
        $location.path($location.path() + '/add');
    };

    $scope.editJobTemplate = function (id) {
        $location.path($location.path() + '/' + id);
    };

    $scope.deleteJobTemplate = function (id, name) {
        var action = function () {
            $('#prompt-modal').modal('hide');
            Wait('start');
            var url = defaultUrl + id + '/';
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    $scope.search(list.iterator);
                })
                .error(function (data) {
                    Wait('stop');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class=\"alert alert-info\">Delete job template ' + name + '?</div>',
            action: action
        });
    };

    $scope.copyJobTemplate = function(id, name){
        var  element,
              buttons = [{
                "label": "Cancel",
                "onClick": function() {
                    $(this).dialog('close');
                },
                "icon": "fa-times",
                "class": "btn btn-default",
                "id": "copy-close-button"
            },{
                "label": "Copy",
                "onClick": function() {
                    copyAction();
                    // setTimeout(function(){
                    //     scope.$apply(function(){
                    //         if(mode==='survey-taker'){
                    //             scope.$emit('SurveyTakerCompleted');
                    //         } else{
                    //             scope.saveSurvey();
                    //         }
                    //     });
                    // });
                },
                "icon":  "fa-copy",
                "class": "btn btn-primary",
                "id": "job-copy-button"
            }],
            copyAction = function () {
                // retrieve the copy of the job template object from the api, then overwrite the name and throw away the id
                Wait('start');
                var url = defaultUrl + id + '/';
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                        data.name = $scope.new_copy_name;
                        delete data.id;
                        $scope.$emit('GoToCopy', data);
                    })
                    .error(function (data) {
                        Wait('stop');
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                    });
            };


        CreateDialog({
            id: 'copy-job-modal'    ,
            title: "Copy",
            scope: $scope,
            buttons: buttons,
            width: 500,
            height: 300,
            minWidth: 200,
            callback: 'CopyDialogReady'
        });

        $('#job_name').text(name);
        $('#copy-job-modal').show();


        if ($scope.removeCopyDialogReady) {
            $scope.removeCopyDialogReady();
        }
        $scope.removeCopyDialogReady = $scope.$on('CopyDialogReady', function() {
            //clear any old remaining text
            $scope.new_copy_name = "" ;
            $scope.copy_form.$setPristine();
            $('#copy-job-modal').dialog('open');
            $('#job-copy-button').attr('ng-disabled', "!copy_form.$valid");
            element = angular.element(document.getElementById('job-copy-button'));
            $compile(element)($scope);

        });

        if ($scope.removeGoToCopy) {
            $scope.removeGoToCopy();
        }
        $scope.removeGoToCopy = $scope.$on('GoToCopy', function(e, data) {
            var url = defaultUrl,
            old_survey_url = (data.related.survey_spec) ? data.related.survey_spec : "" ;
            Rest.setUrl(url);
            Rest.post(data)
                .success(function (data) {
                    if(data.survey_enabled===true){
                        $scope.$emit("CopySurvey", data, old_survey_url);
                    }
                    else {
                        $('#copy-job-modal').dialog('close');
                        Wait('stop');
                        $location.path($location.path() + '/' + data.id);
                    }

                })
                .error(function (data) {
                    Wait('stop');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                });
        });

        if ($scope.removeCopySurvey) {
            $scope.removeCopySurvey();
        }
        $scope.removeCopySurvey = $scope.$on('CopySurvey', function(e, new_data, old_url) {
            // var url = data.related.survey_spec;
            Rest.setUrl(old_url);
            Rest.get()
                .success(function (survey_data) {

                    Rest.setUrl(new_data.related.survey_spec);
                    Rest.post(survey_data)
                    .success(function () {
                        $('#copy-job-modal').dialog('close');
                        Wait('stop');
                        $location.path($location.path() + '/' + new_data.id);
                    })
                    .error(function (data) {
                        Wait('stop');
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + new_data.related.survey_spec + ' failed. DELETE returned status: ' + status });
                    });


                })
                .error(function (data) {
                    Wait('stop');
                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + old_url + ' failed. DELETE returned status: ' + status });
                });

        });

    };

    $scope.submitJob = function (id) {
        PlaybookRun({ scope: $scope, id: id });
    };
}

JobTemplatesList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobTemplateList',
    'generateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
    'ProcessErrors', 'GetBasePath', 'JobTemplateForm', 'CredentialList', 'LookUpInit',
    'PlaybookRun', 'Wait', 'Stream', 'CreateDialog' , '$compile'
];

export function JobTemplatesAdd($scope, $rootScope, $compile, $location, $log, $routeParams, JobTemplateForm,
    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, GetBasePath,
    InventoryList, CredentialList, ProjectList, LookUpInit, md5Setup, ParseTypeChange, Wait, Empty, ToJSON,
    CallbackHelpInit, SurveyControllerInit, Prompt) {

    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('job_templates'),
        form = JobTemplateForm(),
        generator = GenerateForm,
        master = {},
        CloudCredentialList = {},
        selectPlaybook, checkSCMStatus,
        callback;

    CallbackHelpInit({ scope: $scope });
    $scope.can_edit = true;
    generator.inject(form, { mode: 'add', related: false, scope: $scope });

    callback = function() {
        // Make sure the form controller knows there was a change
        $scope[form.name + '_form'].$setDirty();
    };
    $scope.mode = "add";
    $scope.parseType = 'yaml';
    ParseTypeChange({ scope: $scope, field_id: 'job_templates_variables', onChange: callback });

    $scope.job_type_options = [
        { value: 'run', label: 'Run' },
        { value: 'check', label: 'Check' },
        { value: 'scan' , label: 'Scan'}
    ];

    $scope.verbosity_options = [
        { value: 0, label: 'Default' },
        { value: 1, label: 'Verbose' },
        { value: 3, label: 'Debug' }
    ];

    $scope.playbook_options = [];
    $scope.allow_callbacks = 'false';

    generator.reset();
    LoadBreadCrumbs();

    md5Setup({
        scope: $scope,
        master: master,
        check_field: 'allow_callbacks',
        default_val: false
    });

    LookUpInit({
        scope: $scope,
        form: form,
        current_item: ($routeParams.inventory_id !== undefined) ? $routeParams.inventory_id : null,
        list: InventoryList,
        field: 'inventory',
        input_type: "radio"
    });


    // Clone the CredentialList object for use with cloud_credential. Cloning
    // and changing properties to avoid collision.
    jQuery.extend(true, CloudCredentialList, CredentialList);
    CloudCredentialList.name = 'cloudcredentials';
    CloudCredentialList.iterator = 'cloudcredential';

    LookUpInit({
        url: GetBasePath('credentials') + '?cloud=true',
        scope: $scope,
        form: form,
        current_item: null,
        list: CloudCredentialList,
        field: 'cloud_credential',
        hdr: 'Select Cloud Credential',
        input_type: 'radio'
    });

    LookUpInit({
        url: GetBasePath('credentials') + '?kind=ssh',
        scope: $scope,
        form: form,
        current_item: null,
        list: CredentialList,
        field: 'credential',
        hdr: 'Select Machine Credential',
        input_type: "radio"
    });

    SurveyControllerInit({
        scope: $scope,
        parent_scope: $scope
    });



    // Update playbook select whenever project value changes
    selectPlaybook = function (oldValue, newValue) {
        var url;
        if($scope.job_type.value === 'scan' && $scope.project_name === "Default"){
            $scope.playbook_options = ['Default'];
            $scope.playbook = 'Default';
            Wait('stop');
        }
        else if (oldValue !== newValue) {
            if ($scope.project) {
                Wait('start');
                url = GetBasePath('projects') + $scope.project + '/playbooks/';
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                        var i, opts = [];
                        for (i = 0; i < data.length; i++) {
                            opts.push(data[i]);
                        }
                        $scope.playbook_options = opts;
                        Wait('stop');
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to get playbook list for ' + url + '. GET returned status: ' + status });
                    });
            }
        }
    };

    $scope.jobTypeChange = function(){
      if($scope.job_type){
        if($scope.job_type.value === 'scan'){
            // $scope.project_name = 'Default';
            // $scope.project = null;
            $scope.toggleScanInfo();
          }
          else if($scope.project_name === "Default"){
            $scope.project_name = null;
            $scope.playbook_options = [];
            // $scope.playbook = 'null';
            $scope.job_templates_form.playbook.$setPristine();
          }
      }
    };

    $scope.toggleScanInfo = function() {
        $scope.project_name = 'Default';
        if($scope.project === null){
          selectPlaybook();
        }
        else {
          $scope.project = null;
        }
    };

    if ($routeParams.inventory_id) {
        // This means that the job template form was accessed via inventory prop's
        // This also means the job is a scan job.
        $scope.job_type.value = 'scan';
        $scope.jobTypeChange();
        $scope.inventory = $routeParams.inventory_id;
        Rest.setUrl(GetBasePath('inventory') + $routeParams.inventory_id + '/');
        Rest.get()
            .success(function (data) {
                $scope.inventory_name = data.name;
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to lookup inventory: ' + data.id + '. GET returned status: ' + status });
            });
    }

    // Detect and alert user to potential SCM status issues
    checkSCMStatus = function (oldValue, newValue) {
        if (oldValue !== newValue && !Empty($scope.project)) {
            Rest.setUrl(GetBasePath('projects') + $scope.project + '/');
            Rest.get()
                .success(function (data) {
                    var msg;
                    switch (data.status) {
                    case 'failed':
                        msg = "The selected project has a <em>failed</em> status. Review the project's SCM settings" +
                            " and run an update before adding it to a template.";
                        break;
                    case 'never updated':
                        msg = 'The selected project has a <em>never updated</em> status. You will need to run a successful' +
                            ' update in order to selected a playbook. Without a valid playbook you will not be able ' +
                            ' to save this template.';
                        break;
                    case 'missing':
                        msg = 'The selected project has a status of <em>missing</em>. Please check the server and make sure ' +
                            ' the directory exists and file permissions are set correctly.';
                        break;
                    }
                    if (msg) {
                        Alert('Waning', msg, 'alert-info');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to get project ' + $scope.project + '. GET returned status: ' + status });
                });
        }
    };

    // Register a watcher on project_name
    if ($scope.selectPlaybookUnregister) {
        $scope.selectPlaybookUnregister();
    }
    $scope.selectPlaybookUnregister = $scope.$watch('project_name', function (newval, oldval) {
        selectPlaybook(oldval, newval);
        checkSCMStatus(oldval, newval);
    });

    LookUpInit({
        scope: $scope,
        form: form,
        current_item: null,
        list: ProjectList,
        field: 'project',
        input_type: "radio"
    });

    if ($scope.removeSurveySaved) {
        $scope.rmoveSurveySaved();
    }
    $scope.removeSurveySaved = $scope.$on('SurveySaved', function() {
        Wait('stop');
        $scope.survey_exists = true;
        $scope.invalid_survey = false;
        $('#job_templates_survey_enabled_chbox').attr('checked', true);
        $('#job_templates_delete_survey_btn').show();
        $('#job_templates_edit_survey_btn').show();
        $('#job_templates_create_survey_btn').hide();

    });


    function saveCompleted() {
        setTimeout(function() {
          $scope.$apply(function() {
            var base = $location.path().replace(/^\//, '').split('/')[0];
            if (base === 'job_templates') {
                ReturnToCaller();
            }
            else {
                ReturnToCaller(1);
            }
          });
        }, 500);
    }

    if ($scope.removeTemplateSaveSuccess) {
        $scope.removeTemplateSaveSuccess();
    }
    $scope.removeTemplateSaveSuccess = $scope.$on('templateSaveSuccess', function(e, data) {
        Wait('stop');
        if (data.related && data.related.callback) {
            Alert('Callback URL', '<p>Host callbacks are enabled for this template. The callback URL is:</p>'+
                '<p style="padding: 10px 0;"><strong>' + $scope.callback_server_path + data.related.callback + '</strong></p>'+
                '<p>The host configuration key is: <strong>' + data.host_config_key + '</strong></p>', 'alert-info', saveCompleted);
        }
        else {
            saveCompleted();
        }
    });

    // Save
    $scope.formSave = function () {
        $scope.invalid_survey = false;
        if ($scope.removeGatherFormFields) {
            $scope.removeGatherFormFields();
        }
        $scope.removeGatherFormFields = $scope.$on('GatherFormFields', function(e, data) {
            generator.clearApiErrors();
            Wait('start');
            data = {};
            var fld;
            try {
                for (fld in form.fields) {
                    if (form.fields[fld].type === 'select' && fld !== 'playbook') {
                        data[fld] = $scope[fld].value;
                    } else {
                        if (fld !== 'variables') {
                            data[fld] = $scope[fld];
                        }
                    }
                }
                data.extra_vars = ToJSON($scope.parseType, $scope.variables, true);
                if(data.job_type === 'scan' && $scope.default_scan === true){
                  data.project = "";
                  data.playbook = "";
                }
                Rest.setUrl(defaultUrl);
                Rest.post(data)
                    .success(function(data) {
                        $scope.$emit('templateSaveSuccess', data);

                        if(data.survey_enabled===true){
                            //once the job template information is saved we submit the survey info to the correct endpoint
                            var url = data.url+ 'survey_spec/';
                            Rest.setUrl(url);
                            Rest.post({ name: $scope.survey_name, description: $scope.survey_description, spec: $scope.survey_questions })
                                .success(function () {
                                    Wait('stop');

                                })
                                .error(function (data, status) {
                                    ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                                        msg: 'Failed to add new survey. Post returned status: ' + status });
                                });
                        }


                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to add new job template. POST returned status: ' + status
                        });
                    });

            } catch (err) {
                Wait('stop');
                Alert("Error", "Error parsing extra variables. Parser returned: " + err);
            }
        });


        if ($scope.removePromptForSurvey) {
            $scope.removePromptForSurvey();
        }
        $scope.removePromptForSurvey = $scope.$on('PromptForSurvey', function() {
            var action = function () {
                    // $scope.$emit("GatherFormFields");
                    Wait('start');
                    $('#prompt-modal').modal('hide');
                    $scope.addSurvey();

                };
            Prompt({
                hdr: 'Incomplete Survey',
                body: 'Do you want to create a survey before proceeding?',
                action: action
            });
        });

        if($scope.survey_enabled === true && $scope.survey_exists!==true){
            // $scope.$emit("PromptForSurvey");

            // The original design for this was a pop up that would prompt the user if they wanted to create a
            // survey, because they had enabled one but not created it yet. We switched this for now so that
            // an error message would be displayed by the survey buttons that tells the user to add a survey or disabled
            // surveys.
            $scope.invalid_survey = true;
            return;
        } else {
            $scope.$emit("GatherFormFields");
        }


    };

    // Reset
    $scope.formReset = function () {
        // Defaults
        generator.reset();
        //$('#forks-slider').slider("option", "value", $scope.forks);
        for (var fld in master) {
            $scope[fld] = master[fld];
        }
    };
}

JobTemplatesAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobTemplateForm',
    'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope',
    'GetBasePath', 'InventoryList', 'CredentialList', 'ProjectList', 'LookUpInit',
    'md5Setup', 'ParseTypeChange', 'Wait', 'Empty', 'ToJSON', 'CallbackHelpInit', 'SurveyControllerInit', 'Prompt'
];


export function JobTemplatesEdit($scope, $rootScope, $compile, $location, $log, $routeParams, JobTemplateForm, GenerateForm, Rest,
    Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, RelatedPaginateInit, ReturnToCaller, ClearScope, InventoryList,
    CredentialList, ProjectList, LookUpInit, GetBasePath, md5Setup, ParseTypeChange, JobStatusToolTip, FormatDate,
    Wait, Stream, Empty, Prompt, ParseVariableString, ToJSON, SchedulesControllerInit, JobsControllerInit, JobsListUpdate,
    GetChoices, SchedulesListInit, SchedulesList, CallbackHelpInit, PlaybookRun, SurveyControllerInit){

    ClearScope();

    var defaultUrl = GetBasePath('job_templates'),
        generator = GenerateForm,
        form = JobTemplateForm(),
        loadingFinishedCount = 0,
        base = $location.path().replace(/^\//, '').split('/')[0],
        master = {},
        id = $routeParams.template_id,
        relatedSets = {},
        checkSCMStatus, getPlaybooks, callback,
        choicesCount = 0;


    CallbackHelpInit({ scope: $scope });

    SchedulesList.well = false;
    generator.inject(form, { mode: 'edit', related: true, scope: $scope });
    $scope.mode = 'edit';
    $scope.parseType = 'yaml';
    $scope.showJobType = false;

    // Our job type options
    $scope.job_type_options = [
        { value: 'run', label: 'Run' },
        { value: 'check', label: 'Check' },
        { value: 'scan', label: 'Scan'}
    ];

    $scope.verbosity_options = [
        { value: 0, label: 'Default' },
        { value: 1, label: 'Verbose' },
        { value: 3, label: 'Debug' }
    ];

    SurveyControllerInit({
        scope: $scope,
        parent_scope: $scope,
        id: id
    });

    callback = function() {
        // Make sure the form controller knows there was a change
        $scope[form.name + '_form'].$setDirty();
    };

    $scope.playbook_options = null;
    $scope.playbook = null;
    generator.reset();

    getPlaybooks = function (project) {
        var url;
        if($scope.job_type.value === 'scan' && $scope.project_name === "Default"){
            $scope.playbook_options = ['Default'];
            $scope.playbook = 'Default';
            Wait('stop');
        }
        else if (!Empty(project)) {
            url = GetBasePath('projects') + project + '/playbooks/';
            Wait('start');
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    var i;
                    $scope.playbook_options = [];
                    for (i = 0; i < data.length; i++) {
                        $scope.playbook_options.push(data[i]);
                        if (data[i] === $scope.playbook) {
                            $scope.job_templates_form.playbook.$setValidity('required', true);
                        }
                    }
                    if ($scope.playbook) {
                        $scope.$emit('jobTemplateLoadFinished');
                    } else {
                        Wait('stop');
                    }
                })
                .error(function () {
                    Wait('stop');
                    Alert('Missing Playbooks', 'Unable to retrieve the list of playbooks for this project. Choose a different ' +
                        ' project or make the playbooks available on the file system.', 'alert-info');
                });
        }
        else {
            Wait('stop');
        }
    };

    $scope.jobTypeChange = function(){
      if($scope.job_type){
        if($scope.job_type.value === 'scan'){
            // $scope.project_name = 'Default';
            // $scope.project = null;
            $scope.toggleScanInfo();
          }
          else if($scope.project_name === "Default"){
            $scope.project_name = null;
            $scope.playbook_options = [];
            // $scope.playbook = 'null';
            $scope.job_templates_form.playbook.$setPristine();
          }
      }
    };

    $scope.toggleScanInfo = function() {
        $scope.project_name = 'Default';
        if($scope.project === null){
          getPlaybooks();
        }
        else {
          $scope.project = null;
        }
    };

    // Detect and alert user to potential SCM status issues
    checkSCMStatus = function () {
        if (!Empty($scope.project)) {
            Wait('start');
            Rest.setUrl(GetBasePath('projects') + $scope.project + '/');
            Rest.get()
                .success(function (data) {
                    var msg;
                    switch (data.status) {
                    case 'failed':
                        msg = "The selected project has a <em>failed</em> status. Review the project's SCM settings" +
                            " and run an update before adding it to a template.";
                        break;
                    case 'never updated':
                        msg = 'The selected project has a <em>never updated</em> status. You will need to run a successful' +
                            ' update in order to selected a playbook. Without a valid playbook you will not be able ' +
                            ' to save this template.';
                        break;
                    case 'missing':
                        msg = 'The selected project has a status of <em>missing</em>. Please check the server and make sure ' +
                            ' the directory exists and file permissions are set correctly.';
                        break;
                    }
                    Wait('stop');
                    if (msg) {
                        Alert('Waning', msg, 'alert-info');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, form, { hdr: 'Error!', msg: 'Failed to get project ' + $scope.project +
                        '. GET returned status: ' + status });
                });
        }
    };

    if ($scope.removerelatedschedules) {
        $scope.removerelatedschedules();
    }
    $scope.removerelatedschedules = $scope.$on('relatedschedules', function() {
        SchedulesListInit({
            scope: $scope,
            list: SchedulesList,
            choices: null,
            related: true
        });
    });

    // Register a watcher on project_name. Refresh the playbook list on change.
    if ($scope.watchProjectUnregister) {
        $scope.watchProjectUnregister();
    }
    $scope.watchProjectUnregister = $scope.$watch('project', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!Empty(oldValue)) {
                $scope.playbook = null;
            }
            getPlaybooks($scope.project);
            checkSCMStatus();
        }
    });



    // Turn off 'Wait' after both cloud credential and playbook list come back
    if ($scope.removeJobTemplateLoadFinished) {
        $scope.removeJobTemplateLoadFinished();
    }
    $scope.removeJobTemplateLoadFinished = $scope.$on('jobTemplateLoadFinished', function () {
        loadingFinishedCount++;
        if (loadingFinishedCount >= 2) {
            // The initial template load finished. Now load related jobs, which
            // will turn off the 'working' spinner.
            for (var set in relatedSets) {
                $scope.search(relatedSets[set].iterator);
            }
            SchedulesControllerInit({
                scope: $scope,
                parent_scope: $scope,
                iterator: 'schedule'
            });
        }
    });

    // Set the status/badge for each related job
    if ($scope.removeRelatedCompletedJobs) {
        $scope.removeRelatedCompletedJobs();
    }
    $scope.removeRelatedCompletedJobs = $scope.$on('relatedcompleted_jobs', function () {
        JobsControllerInit({
            scope: $scope,
            parent_scope: $scope,
            iterator: form.related.completed_jobs.iterator
        });
        JobsListUpdate({
            scope: $scope,
            parent_scope: $scope,
            list: form.related.completed_jobs
        });
    });

    if ($scope.cloudCredentialReadyRemove) {
        $scope.cloudCredentialReadyRemove();
    }
    $scope.cloudCredentialReadyRemove = $scope.$on('cloudCredentialReady', function (e, name) {
        var CloudCredentialList = {};
        $scope.cloud_credential_name = name;
        master.cloud_credential_name = name;
        // Clone the CredentialList object for use with cloud_credential. Cloning
        // and changing properties to avoid collision.
        jQuery.extend(true, CloudCredentialList, CredentialList);
        CloudCredentialList.name = 'cloudcredentials';
        CloudCredentialList.iterator = 'cloudcredential';
        LookUpInit({
            url: GetBasePath('credentials') + '?cloud=true',
            scope: $scope,
            form: form,
            current_item: $scope.cloud_credential,
            list: CloudCredentialList,
            field: 'cloud_credential',
            hdr: 'Select Cloud Credential',
            input_type: "radio"
        });
        $scope.$emit('jobTemplateLoadFinished');
    });


    // Retrieve each related set and populate the playbook list
    if ($scope.jobTemplateLoadedRemove) {
        $scope.jobTemplateLoadedRemove();
    }
    $scope.jobTemplateLoadedRemove = $scope.$on('jobTemplateLoaded', function (e, related_cloud_credential, masterObject) {
        var dft;
        master = masterObject;
        getPlaybooks($scope.project);

        dft = ($scope.host_config_key === "" || $scope.host_config_key === null) ? 'false' : 'true';
        md5Setup({
            scope: $scope,
            master: master,
            check_field: 'allow_callbacks',
            default_val: dft
        });

        ParseTypeChange({ scope: $scope, field_id: 'job_templates_variables', onChange: callback });

        if (related_cloud_credential) {
            Rest.setUrl(related_cloud_credential);
            Rest.get()
                .success(function (data) {
                    $scope.$emit('cloudCredentialReady', data.name);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, null, {hdr: 'Error!',
                        msg: 'Failed to related cloud credential. GET returned status: ' + status });
                });
        } else {
            // No existing cloud credential
            $scope.$emit('cloudCredentialReady', null);
        }
    });

    Wait('start');

    if ($scope.removeEnableSurvey) {
        $scope.removeEnableSurvey();
    }
    $scope.removeEnableSurvey = $scope.$on('EnableSurvey', function(fld) {

        $('#job_templates_survey_enabled_chbox').attr('checked', $scope[fld]);
        Rest.setUrl(defaultUrl + id+ '/survey_spec/');
        Rest.get()
            .success(function (data) {
                if(!data || !data.name){
                    $('#job_templates_delete_survey_btn').hide();
                    $('#job_templates_edit_survey_btn').hide();
                    $('#job_templates_create_survey_btn').show();
                }
                else {
                    $scope.survey_exists = true;
                    $('#job_templates_delete_survey_btn').show();
                    $('#job_templates_edit_survey_btn').show();
                    $('#job_templates_create_survey_btn').hide();
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to retrieve job template: ' + $routeParams.template_id + '. GET status: ' + status
                });
            });
    });

    if ($scope.removeSurveySaved) {
        $scope.rmoveSurveySaved();
    }
    $scope.removeSurveySaved = $scope.$on('SurveySaved', function() {
        Wait('stop');
        $scope.survey_exists = true;
        $scope.invalid_survey = false;
        $('#job_templates_survey_enabled_chbox').attr('checked', true);
        $('#job_templates_delete_survey_btn').show();
        $('#job_templates_edit_survey_btn').show();
        $('#job_templates_create_survey_btn').hide();

    });

    if ($scope.removeLoadJobs) {
        $scope.rmoveLoadJobs();
    }
    $scope.removeLoadJobs = $scope.$on('LoadJobs', function() {
        $scope.fillJobTemplate();
    });

    if ($scope.removeChoicesReady) {
        $scope.removeChoicesReady();
    }
    $scope.removeChoicesReady = $scope.$on('choicesReady', function() {
        choicesCount++;
        if (choicesCount === 2) {
            $scope.$emit('LoadJobs');
        }
    });

    GetChoices({
        scope: $scope,
        url: GetBasePath('unified_jobs'),
        field: 'status',
        variable: 'status_choices',
        callback: 'choicesReady'
    });

    GetChoices({
        scope: $scope,
        url: GetBasePath('unified_jobs'),
        field: 'type',
        variable: 'type_choices',
        callback: 'choicesReady'
    });

    function saveCompleted() {
        setTimeout(function() {
          $scope.$apply(function() {
            var base = $location.path().replace(/^\//, '').split('/')[0];
            if (base === 'job_templates') {
                ReturnToCaller();
            }
            else {
                ReturnToCaller(1);
            }
          });
        }, 500);
    }

    if ($scope.removeTemplateSaveSuccess) {
        $scope.removeTemplateSaveSuccess();
    }
    $scope.removeTemplateSaveSuccess = $scope.$on('templateSaveSuccess', function(e, data) {
        Wait('stop');
        if ($scope.allow_callbacks && ($scope.host_config_key !== master.host_config_key || $scope.callback_url !== master.callback_url)) {
            if (data.related && data.related.callback) {
                Alert('Callback URL', '<p>Host callbacks are enabled for this template. The callback URL is:</p>'+
                    '<p style="padding: 10px 0;"><strong>' + $scope.callback_server_path + data.related.callback + '</strong></p>'+
                    '<p>The host configuration key is: <strong>' + data.host_config_key + '</strong></p>', 'alert-info', saveCompleted);
            }
            else {
                saveCompleted();
            }
        }
        else {
            saveCompleted();
        }
    });



    // Save changes to the parent
    $scope.formSave = function () {
        $scope.invalid_survey = false;
        if ($scope.removeGatherFormFields) {
            $scope.removeGatherFormFields();
        }
        $scope.removeGatherFormFields = $scope.$on('GatherFormFields', function(e, data) {
            generator.clearApiErrors();
            Wait('start');
            data = {};
            var fld;
            try {
                // Make sure we have valid variable data
                data.extra_vars = ToJSON($scope.parseType, $scope.variables, true);
                if(data.extra_vars === undefined ){
                    throw 'undefined variables';
                }
                for (fld in form.fields) {
                    if (form.fields[fld].type === 'select' && fld !== 'playbook') {
                        data[fld] = $scope[fld].value;
                    } else {
                        if (fld !== 'variables' && fld !== 'callback_url') {
                            data[fld] = $scope[fld];
                        }
                    }
                }
                Rest.setUrl(defaultUrl + id + '/');
                Rest.put(data)
                    .success(function (data) {
                        $scope.$emit('templateSaveSuccess', data);
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                            msg: 'Failed to update job template. PUT returned status: ' + status });
                    });

            } catch (err) {
                Wait('stop');
                Alert("Error", "Error parsing extra variables. Parser returned: " + err);
            }
        });


        if ($scope.removePromptForSurvey) {
            $scope.removePromptForSurvey();
        }
        $scope.removePromptForSurvey = $scope.$on('PromptForSurvey', function() {
            var action = function () {
                    // $scope.$emit("GatherFormFields");
                    Wait('start');
                    $('#prompt-modal').modal('hide');
                    $scope.addSurvey();

                };
            Prompt({
                hdr: 'Incomplete Survey',
                body: 'Do you want to create a survey before proceeding?',
                action: action
            });
        });

        if($scope.survey_enabled === true && $scope.survey_exists!==true){
            // $scope.$emit("PromptForSurvey");

            // The original design for this was a pop up that would prompt the user if they wanted to create a
            // survey, because they had enabled one but not created it yet. We switched this for now so that
            // an error message would be displayed by the survey buttons that tells the user to add a survey or disabled
            // surveys.
            $scope.invalid_survey = true;
            return;
        } else {
            $scope.$emit("GatherFormFields");
        }

    };

    $scope.showActivity = function () {
        Stream({
            scope: $scope
        });
    };

    // Cancel
    $scope.formReset = function () {
        generator.reset();
        for (var fld in master) {
            $scope[fld] = master[fld];
        }
        $scope.parseType = 'yaml';
        ParseTypeChange({ scope: $scope, field_id: 'job_templates_variables', onChange: callback });
        $('#forks-slider').slider("option", "value", $scope.forks);
    };

    // Related set: Add button
    $scope.add = function (set) {
        $rootScope.flashMessage = null;
        $location.path('/' + base + '/' + $routeParams.template_id + '/' + set);
    };

    // Related set: Edit button
    $scope.edit = function (set, id) {
        $rootScope.flashMessage = null;
        $location.path('/' + set + '/' + id);
    };

    // Launch a job using the selected template
    $scope.launch = function() {

        if ($scope.removePromptForSurvey) {
            $scope.removePromptForSurvey();
        }
        $scope.removePromptForSurvey = $scope.$on('PromptForSurvey', function() {
            var action = function () {
                    // $scope.$emit("GatherFormFields");
                    Wait('start');
                    $('#prompt-modal').modal('hide');
                    $scope.addSurvey();

                };
            Prompt({
                hdr: 'Incomplete Survey',
                body: 'Do you want to create a survey before proceeding?',
                action: action
            });
        });

        if($scope.survey_enabled === true && $scope.survey_exists!==true){
            $scope.$emit("PromptForSurvey");
        }
        else {
            PlaybookRun({
                scope: $scope,
                id: id
            });
        }
    };

    // handler for 'Enable Survey' button
    $scope.surveyEnabled = function(){
        Rest.setUrl(defaultUrl + id+ '/');
        Rest.patch({"survey_enabled": $scope.survey_enabled})
            .success(function (data) {

                if(Empty(data.summary_fields.survey)){
                    $('#job_templates_delete_survey_btn').hide();
                    $('#job_templates_edit_survey_btn').hide();
                    $('#job_templates_create_survey_btn').show();
                }
                else{
                    $scope.survey_exists = true;
                    $('#job_templates_delete_survey_btn').show();
                    $('#job_templates_edit_survey_btn').show();
                    $('#job_templates_create_survey_btn').hide();
                }
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, {
                    hdr: 'Error!',
                    msg: 'Failed to retrieve save survey_enabled: ' + $routeParams.template_id + '. GET status: ' + status
                });
            });
    };


}

JobTemplatesEdit.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobTemplateForm',
    'GenerateForm', 'Rest', 'Alert',  'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 'RelatedPaginateInit',
    'ReturnToCaller', 'ClearScope', 'InventoryList', 'CredentialList', 'ProjectList', 'LookUpInit',
    'GetBasePath', 'md5Setup', 'ParseTypeChange', 'JobStatusToolTip', 'FormatDate', 'Wait', 'Stream', 'Empty', 'Prompt',
    'ParseVariableString', 'ToJSON', 'SchedulesControllerInit', 'JobsControllerInit', 'JobsListUpdate', 'GetChoices',
    'SchedulesListInit', 'SchedulesList', 'CallbackHelpInit', 'PlaybookRun' , 'SurveyControllerInit'
];
