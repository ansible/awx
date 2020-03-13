import templateUrl from './relaunchButton.partial.html';

const atRelaunch = {
    templateUrl,
    bindings: {
        job: '<'
    },
    controller: ['ProcessErrors', 'AdhocRun', 'ComponentsStrings',
        'ProjectModel', 'InventorySourceModel', 'WorkflowJobModel', 'Alert',
        'AdHocCommandModel', 'JobModel', 'JobTemplateModel', 'PromptService',
        '$state', '$q', '$scope', atRelaunchCtrl
    ],
    controllerAs: 'vm'
};

function atRelaunchCtrl (
    ProcessErrors, AdhocRun, strings,
    Project, InventorySource, WorkflowJob, Alert,
    AdHocCommand, Job, JobTemplate, PromptService,
    $state, $q, $scope
) {
    const vm = this;
    vm.strings = strings;
    const jobObj = new Job();
    const jobTemplate = new JobTemplate();

    const transitionOptions = { reload: true };

    if ($state.includes('output')) {
        transitionOptions.inherit = false;
        transitionOptions.location = 'replace';
    }

    const updateTooltip = () => {
        if (vm.job.type === 'job' && vm.job.status === 'failed') {
            vm.tooltip = strings.get('relaunch.HOSTS');
        } else {
            vm.tooltip = strings.get('relaunch.DEFAULT');
        }
    };

    const checkRelaunchPlaybook = (option) => {
        jobObj.getRelaunch({
            id: vm.job.id
        }).then((getRelaunchRes) => {
            if (
                getRelaunchRes.data.passwords_needed_to_start &&
                getRelaunchRes.data.passwords_needed_to_start.length > 0
            ) {
                const jobPromises = [
                    jobObj.request('get', vm.job.id),
                    jobTemplate.optionsLaunch(vm.job.unified_job_template),
                    jobObj.getCredentials(vm.job.id)
                ];

                $q.all(jobPromises)
                    .then(([jobRes, launchOptions, jobCreds]) => {
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
                            job: vm.job.id,
                            relaunchHostType: option ? (option.value) : null,
                            prompts: {
                                credentials: {
                                    value: populatedJob.summary_fields.credentials ?
                                        _.merge(
                                            jobCreds.data.results,
                                            populatedJob.summary_fields.credentials
                                        ) : []
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
                                },
                                scmBranch: {
                                    value: populatedJob.scm_branch
                                }
                            },
                            triggerModalOpen: true
                        };
                    });
            } else {
                const launchParams = {
                    id: vm.job.id,
                };

                if (_.has(option, 'value')) {
                    launchParams.relaunchData = {
                        hosts: option.value
                    };
                }

                jobObj.postRelaunch(launchParams)
                    .then((launchRes) => {
                        if (!$state.is('jobs')) {
                            const relaunchType = launchRes.data.type === 'job' ? 'playbook' : launchRes.data.type;
                            $state.go('output', { id: launchRes.data.id, type: relaunchType }, transitionOptions);
                        }
                    }).catch(({ data, status, config }) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: strings.get('error.HEADER'),
                            msg: strings.get('error.CALL', { path: `${config.url}`, status })
                        });
                    });
            }
        });
    };

    vm.$onInit = () => {
        vm.showRelaunch = vm.job.type !== 'system_job' && vm.job.summary_fields.user_capabilities.start;

        vm.icon = 'icon-launch';
        vm.dropdownTitle = strings.get('relaunch.DROPDOWN_TITLE');
        vm.dropdownOptions = [
            {
                name: strings.get('relaunch.ALL'),
                icon: 'icon-host-all',
                value: 'all'
            },
            {
                name: strings.get('relaunch.FAILED'),
                icon: 'icon-host-failed',
                value: 'failed'
            }
        ];

        updateTooltip();

        $scope.$watch('vm.job.status', () => {
            updateTooltip();
        });
    };

    vm.relaunchJob = () => {
        if (vm.job.type === 'inventory_update') {
            const inventorySource = new InventorySource();

            inventorySource.getUpdate(vm.job.inventory_source)
                .then((getUpdateRes) => {
                    if (getUpdateRes.data.can_update) {
                        inventorySource.postUpdate(vm.job.inventory_source)
                            .then((postUpdateRes) => {
                                if (!$state.is('jobs')) {
                                    $state.go('output', { id: postUpdateRes.data.id, type: 'inventory' }, transitionOptions);
                                }
                            }).catch(({ data, status, config }) => {
                                ProcessErrors($scope, data, status, null, {
                                    hdr: strings.get('error.HEADER'),
                                    msg: strings.get('error.CALL', { path: `${config.url}`, status })
                                });
                            });
                    } else {
                        Alert(
                            'Permission Denied', 'You do not have permission to sync this inventory source. Please contact your system administrator.',
                            'alert-danger'
                        );
                    }
                });
        } else if (vm.job.type === 'project_update') {
            const project = new Project();

            project.getUpdate(vm.job.project)
                .then((getUpdateRes) => {
                    if (getUpdateRes.data.can_update) {
                        project.postUpdate(vm.job.project)
                            .then((postUpdateRes) => {
                                if (!$state.is('jobs')) {
                                    $state.go('output', { id: postUpdateRes.data.id, type: 'project' }, transitionOptions);
                                }
                            }).catch(({ data, status, config }) => {
                                ProcessErrors($scope, data, status, null, {
                                    hdr: strings.get('error.HEADER'),
                                    msg: strings.get('error.CALL', { path: `${config.url}`, status })
                                });
                            });
                    } else {
                        Alert(
                            'Permission Denied', 'You do not have access to update this project. Please contact your system administrator.',
                            'alert-danger'
                        );
                    }
                });
        } else if (vm.job.type === 'workflow_job') {
            const workflowJob = new WorkflowJob();

            workflowJob.postRelaunch({
                id: vm.job.id
            }).then((launchRes) => {
                if (!$state.is('jobs')) {
                    $state.go('workflowResults', { id: launchRes.data.id }, transitionOptions);
                }
            }).catch(({ data, status, config }) => {
                ProcessErrors($scope, data, status, null, {
                    hdr: strings.get('error.HEADER'),
                    msg: strings.get('error.CALL', { path: `${config.url}`, status })
                });
            });
        } else if (vm.job.type === 'ad_hoc_command') {
            const adHocCommand = new AdHocCommand();

            adHocCommand.getRelaunch({
                id: vm.job.id
            }).then((getRelaunchRes) => {
                if (
                    getRelaunchRes.data.passwords_needed_to_start &&
                    getRelaunchRes.data.passwords_needed_to_start.length > 0
                ) {
                    AdhocRun({ scope: $scope, project_id: vm.job.id, relaunch: true });
                } else {
                    adHocCommand.postRelaunch({
                        id: vm.job.id
                    }).then((launchRes) => {
                        if (!$state.is('jobs')) {
                            $state.go('output', { id: launchRes.data.id, type: 'command' }, transitionOptions);
                        }
                    }).catch(({ data, status, config }) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: strings.get('error.HEADER'),
                            msg: strings.get('error.CALL', { path: `${config.url}`, status })
                        });
                    });
                }
            });
        } else if (vm.job.type === 'job') {
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
            if (!$state.is('jobs')) {
                $state.go('output', { id: launchRes.data.job, type: 'playbook' }, transitionOptions);
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
