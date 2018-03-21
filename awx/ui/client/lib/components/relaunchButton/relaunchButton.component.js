import templateUrl from './relaunchButton.partial.html';

const atRelaunch = {
    templateUrl,
    bindings: {
        state: '<'
    },
    controller: ['ProcessErrors', 'AdhocRun', 'ComponentsStrings',
        'ProjectModel', 'InventorySourceModel', 'WorkflowJobModel', 'Alert',
        'AdHocCommandModel', 'JobModel', 'JobTemplateModel', 'PromptService',
        'GetBasePath', '$state', '$q', '$scope', atRelaunchCtrl
    ],
    controllerAs: 'vm'
};

function atRelaunchCtrl (
    ProcessErrors, AdhocRun, strings,
    Project, InventorySource, WorkflowJob, Alert,
    AdHocCommand, Job, JobTemplate, PromptService,
    GetBasePath, $state, $q, $scope
) {
    const vm = this;
    const scope = $scope.$parent;
    const job = _.get(scope, 'job') || _.get(scope, 'completed_job');
    const jobObj = new Job();
    const jobTemplate = new JobTemplate();

    const checkRelaunchPlaybook = (option) => {
        jobObj.getRelaunch({
            id: job.id
        }).then((getRelaunchRes) => {
            if (
                getRelaunchRes.data.passwords_needed_to_start &&
                getRelaunchRes.data.passwords_needed_to_start.length > 0
            ) {
                const jobPromises = [
                    jobObj.request('get', job.id),
                    jobTemplate.optionsLaunch(job.unified_job_template)
                ];

                $q.all(jobPromises)
                    .then(([jobRes, launchOptions]) => {
                        const populatedJob = jobRes.data;
                        const jobTypeChoices = _.get(
                            launchOptions,
                            'data.actions.POST.job_type.choices',
                            []
                        ).map(c => ({ label: c[1], value: c[0] }));
                        const verbosityChoices = _.get(
                            launchOptions,
                            'data.actions.POST.verbosity.choices',
                            []
                        ).map(c => ({ label: c[1], value: c[0] }));
                        const verbosity = _.find(
                            verbosityChoices,
                            item => item.value === populatedJob.verbosity
                        );
                        const jobType = _.find(
                            jobTypeChoices,
                            item => item.value === populatedJob.job_type
                        );

                        vm.promptData = {
                            launchConf: {
                                passwords_needed_to_start:
                                    getRelaunchRes.data.passwords_needed_to_start
                            },
                            launchOptions: launchOptions.data,
                            job: job.id,
                            relaunchHostType: option ? (option.name).toLowerCase() : null,
                            prompts: {
                                credentials: {
                                    value: populatedJob.summary_fields.credentials || []
                                },
                                variables: {
                                    value: populatedJob.extra_vars
                                },
                                inventory: {
                                    value: populatedJob.summary_fields.inventory || null
                                },
                                verbosity: {
                                    value: verbosity,
                                    choices: verbosityChoices
                                },
                                jobType: {
                                    value: jobType,
                                    choices: jobTypeChoices
                                },
                                limit: {
                                    value: populatedJob.limit
                                },
                                tags: {
                                    value: populatedJob.job_tags
                                },
                                skipTags: {
                                    value: populatedJob.skip_tags
                                },
                                diffMode: {
                                    value: populatedJob.diff_mode
                                }
                            },
                            triggerModalOpen: true
                        };
                    });
            } else {
                jobObj.postRelaunch({
                    id: job.id
                }).then((launchRes) => {
                    if (!$state.includes('jobs')) {
                        $state.go('jobResult', { id: launchRes.data.id }, { reload: true });
                    }
                });
            }
        });
    };

    vm.$onInit = () => {
        vm.showRelaunch = job.type !== 'system_job' && job.summary_fields.user_capabilities.start;
        vm.showDropdown = job.type === 'job' && job.failed === true;

        vm.createDropdown();
        vm.createTooltips();
    };

    vm.createDropdown = () => {
        vm.icon = 'icon-launch';
        vm.dropdownTitle = strings.get('relaunch.DROPDOWN_TITLE');
        vm.dropdownOptions = [
            {
                name: strings.get('relaunch.ALL'),
                icon: 'icon-host-all'
            },
            {
                name: strings.get('relaunch.FAILED'),
                icon: 'icon-host-failed'
            }
        ];
    };

    vm.createTooltips = () => {
        if (vm.showDropdown) {
            vm.tooltip = strings.get('relaunch.HOSTS');
        } else {
            vm.tooltip = strings.get('relaunch.DEFAULT');
        }
    };

    vm.relaunchJob = () => {
        if (job.type === 'inventory_update') {
            const inventorySource = new InventorySource();

            inventorySource.getUpdate(job.inventory_source)
                .then((getUpdateRes) => {
                    if (getUpdateRes.data.can_update) {
                        inventorySource.postUpdate(job.inventory_source)
                            .then((postUpdateRes) => {
                                if (!$state.includes('jobs')) {
                                    $state.go('inventorySyncStdout', { id: postUpdateRes.data.id }, { reload: true });
                                }
                            });
                    } else {
                        Alert(
                            'Permission Denied', 'You do not have permission to sync this inventory source. Please contact your system administrator.',
                            'alert-danger'
                        );
                    }
                });
        } else if (job.type === 'project_update') {
            const project = new Project();

            project.getUpdate(job.project)
                .then((getUpdateRes) => {
                    if (getUpdateRes.data.can_update) {
                        project.postUpdate(job.project)
                            .then((postUpdateRes) => {
                                if (!$state.includes('jobs')) {
                                    $state.go('scmUpdateStdout', { id: postUpdateRes.data.id }, { reload: true });
                                }
                            });
                    } else {
                        Alert(
                            'Permission Denied', 'You do not have access to update this project. Please contact your system administrator.',
                            'alert-danger'
                        );
                    }
                });
        } else if (job.type === 'workflow_job') {
            const workflowJob = new WorkflowJob();

            workflowJob.postRelaunch({
                id: job.id
            }).then((launchRes) => {
                if (!$state.includes('jobs')) {
                    $state.go('workflowResults', { id: launchRes.data.id }, { reload: true });
                }
            });
        } else if (job.type === 'ad_hoc_command') {
            const adHocCommand = new AdHocCommand();

            adHocCommand.getRelaunch({
                id: job.id
            }).then((getRelaunchRes) => {
                if (
                    getRelaunchRes.data.passwords_needed_to_start &&
                    getRelaunchRes.data.passwords_needed_to_start.length > 0
                ) {
                    AdhocRun({ scope, project_id: job.id, relaunch: true });
                } else {
                    adHocCommand.postRelaunch({
                        id: job.id
                    }).then((launchRes) => {
                        if (!$state.includes('jobs')) {
                            $state.go('adHocJobStdout', { id: launchRes.data.id }, { reload: true });
                        }
                    });
                }
            });
        } else if (job.type === 'job') {
            checkRelaunchPlaybook();
        }
    };

    vm.relaunchOn = (option) => {
        checkRelaunchPlaybook(option);
    };

    vm.relaunchJobWithPassword = () => {
        jobObj.postRelaunch({
            id: vm.promptData.job,
            relaunchData: PromptService.bundlePromptDataForRelaunch(vm.promptData)
        }).then((launchRes) => {
            if (!$state.includes('jobs')) {
                $state.go('jobResult', { id: launchRes.data.job }, { reload: true });
            }
        }).catch(({ data, status }) => {
            ProcessErrors($scope, data, status, null, {
                hdr: 'Error!',
                msg: `Error relaunching job. POST returned status: ${status}`
            });
        });
    };
}

export default atRelaunch;
