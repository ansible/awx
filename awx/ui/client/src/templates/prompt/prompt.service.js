function PromptService (Empty, $filter)  {

    this.processPromptValues = (params) => {
        const prompts = {
            credentials: {},
            inventory: {},
            variables: {},
            verbosity: {},
            jobType: {},
            limit: {},
            tags: {},
            skipTags: {},
            diffMode: {},
            scmBranch: {}
        };

        prompts.credentials.value = _.has(params, 'launchConf.defaults.credentials') ? _.cloneDeep(params.launchConf.defaults.credentials) : [];
        prompts.inventory.value = _.has(params, 'currentValues.summary_fields.inventory') ? params.currentValues.summary_fields.inventory : (_.has(params, 'launchConf.defaults.inventory') ? params.launchConf.defaults.inventory : null);

        const skipTags = _.has(params, 'currentValues.skip_tags') && params.currentValues.skip_tags ? params.currentValues.skip_tags : (_.has(params, 'launchConf.defaults.skip_tags') ? params.launchConf.defaults.skip_tags : "");
        const jobTags = _.has(params, 'currentValues.job_tags') && params.currentValues.job_tags ? params.currentValues.job_tags : (_.has(params, 'launchConf.defaults.job_tags') ? params.launchConf.defaults.job_tags : "");

        let extraVars = '';

        const hasCurrentExtraVars = _.get(params, 'currentValues.extra_data'),
              hasDefaultExtraVars = _.get(params, 'launchConf.defaults.extra_vars');

        if(hasCurrentExtraVars && hasDefaultExtraVars) {
            let currentExtraVars = {};
            let defaultExtraVars = {};
            if (typeof params.currentValues.extra_data === 'object') {
                currentExtraVars = params.currentValues.extra_data;
            } else if (typeof params.currentValues.extra_data === 'string') {
                currentExtraVars = jsyaml.safeDump(params.currentValues.extra_data);
            }

            if (typeof params.launchConf.defaults.extra_vars === 'object') {
                defaultExtraVars = params.launchConf.defaults.extra_vars;
            } else if (typeof params.launchConf.defaults.extra_vars === 'string') {
                defaultExtraVars = jsyaml.safeLoad(params.launchConf.defaults.extra_vars);
            }
            extraVars = '---\n' + jsyaml.safeDump(_.merge(defaultExtraVars, currentExtraVars));
        } else if(hasCurrentExtraVars) {
            if (typeof params.currentValues.extra_data === 'object') {
                extraVars = '---\n' + jsyaml.safeDump(params.currentValues.extra_data);
            } else if (typeof params.currentValues.extra_data === 'string') {
                extraVars = params.currentValues.extra_data;
            }
        } else if(hasDefaultExtraVars) {
            extraVars = params.launchConf.defaults.extra_vars;
        }

        prompts.variables.value = extraVars && extraVars !== '' ? extraVars : '---\n';
        prompts.verbosity.choices = _.get(params, 'launchOptions.actions.POST.verbosity.choices', []).map(c => ({label: c[1], value: c[0]}));
        prompts.verbosity.value = _.has(params, 'currentValues.verbosity') && params.currentValues.verbosity ? _.find(prompts.verbosity.choices, item => item.value === params.currentValues.verbosity) : _.find(prompts.verbosity.choices, item => item.value === params.launchConf.defaults.verbosity);
        prompts.jobType.choices = _.get(params, 'launchOptions.actions.POST.job_type.choices', []).map(c => ({label: c[1], value: c[0]}));
        prompts.jobType.value = _.has(params, 'currentValues.job_type') && params.currentValues.job_type ? _.find(prompts.jobType.choices, item => item.value === params.currentValues.job_type) : _.find(prompts.jobType.choices, item => item.value === params.launchConf.defaults.job_type);
        prompts.limit.value = _.has(params, 'currentValues.limit') && params.currentValues.limit ? params.currentValues.limit : (_.has(params, 'launchConf.defaults.limit') ? params.launchConf.defaults.limit : "");
        prompts.tags.value = (jobTags && jobTags !== "") ? jobTags.split(',').map((i) => ({name: i, label: i, value: i})) : [];
        prompts.skipTags.value = (skipTags && skipTags !== "") ? skipTags.split(',').map((i) => ({name: i, label: i, value: i})) : [];
        prompts.diffMode.value = _.has(params, 'currentValues.diff_mode') && typeof params.currentValues.diff_mode === 'boolean' ? params.currentValues.diff_mode : (_.has(params, 'launchConf.defaults.diff_mode') ? params.launchConf.defaults.diff_mode : null);
        prompts.scmBranch.value = _.has(params, 'currentValues.scm_branch') && params.currentValues.scm_branch ? params.currentValues.scm_branch : (_.has(params, 'launchConf.defaults.scm_branch') ? params.launchConf.defaults.scm_branch : "");
        return prompts;
    };

    this.processSurveyQuestions = (params) => {

        let missingSurveyValue = false;

        for(let i=0; i<params.surveyQuestions.length; i++){
            var question = params.surveyQuestions[i];
            question.index = i;
            question.question_name = $filter('sanitize')(question.question_name);
            question.question_description = (question.question_description) ? $filter('sanitize')(question.question_description) : undefined;

            if(question.type === "textarea" && (!Empty(question.default_textarea) || (params.extra_data && params.extra_data[question.variable]))) {
                if(params.extra_data && params.extra_data[question.variable]) {
                    question.model = params.extra_data[question.variable];
                    delete params.extra_data[question.variable];
                } else {
                    question.model = angular.copy(question.default_textarea);
                }
            }
            else if(question.type === "multiselect") {
                if(params.extra_data && params.extra_data[question.variable]) {
                    question.model = params.extra_data[question.variable];
                    delete params.extra_data[question.variable];
                } else {
                    question.model = question.default.split(/\n/);
                }
                question.choices = typeof question.choices.split === 'function' ? question.choices.split(/\n/) : question.choices;
            }
            else if(question.type === "multiplechoice") {
                if(params.extra_data && params.extra_data[question.variable]) {
                    question.model = params.extra_data[question.variable];
                    delete params.extra_data[question.variable];
                } else {
                    question.model = question.default ? angular.copy(question.default) : "";
                }

                question.choices = typeof question.choices.split === 'function' ? question.choices.split(/\n/) : question.choices;

                // Add a default empty string option to the choices array.  If this choice is
                // selected then the extra var will not be sent when we POST to the launch
                // endpoint
                if(!question.required) {
                    question.choices.unshift('');
                }
            }
            else if(question.type === "float"){
                if(params.extra_data && params.extra_data[question.variable]) {
                    question.model = !Empty(params.extra_data[question.variable]) ? params.extra_data[question.variable] : ((!Empty(question.default)) ? angular.copy(question.default) : (!Empty(question.default_float)) ? angular.copy(question.default_float) : "");
                    delete params.extra_data[question.variable];
                } else {
                    question.model = (!Empty(question.default)) ? angular.copy(question.default) : (!Empty(question.default_float)) ? angular.copy(question.default_float) : "";
                }
            }
            else {
                if(params.extra_data && params.extra_data[question.variable]) {
                    question.model = params.extra_data[question.variable];
                    delete params.extra_data[question.variable];
                } else {
                    question.model = question.default ? angular.copy(question.default) : "";
                }
            }

            if(question.type === "text" || question.type === "textarea" || question.type === "password") {
                question.minlength = (!Empty(question.min)) ? Number(question.min) : "";
                question.maxlength = (!Empty(question.max)) ? Number(question.max) : "" ;
            }
            else if(question.type === "integer") {
                question.minValue = (!Empty(question.min)) ? Number(question.min) : "";
                question.maxValue = (!Empty(question.max)) ? Number(question.max) : "" ;
            }
            else if(question.type === "float") {
                question.minValue = (!Empty(question.min)) ? question.min : "";
                question.maxValue = (!Empty(question.max)) ? question.max : "" ;
            }

            if(question.required && (Empty(question.model) || question.model === [])) {
                missingSurveyValue = true;
            }
        }

        return {
            surveyQuestions: params.surveyQuestions,
            extra_data: params.extra_data,
            missingSurveyValue: missingSurveyValue
        };
    };

    this.bundlePromptDataForLaunch = (promptData) => {
        const launchData = {
            extra_vars: promptData.extraVars
        };

        if (promptData.launchConf.ask_tags_on_launch){
            launchData.job_tags = promptData.prompts.tags.value.map(a => a.value).join();
        }
        if (promptData.launchConf.ask_skip_tags_on_launch){
            launchData.skip_tags = promptData.prompts.skipTags.value.map(a => a.value).join();
        }
        if (promptData.launchConf.ask_limit_on_launch && _.has(promptData, 'prompts.limit.value')){
            launchData.limit = promptData.prompts.limit.value;
        }
        if (promptData.launchConf.ask_job_type_on_launch && _.has(promptData, 'prompts.jobType.value.value')) {
            launchData.job_type = promptData.prompts.jobType.value.value;
        }
        if (promptData.launchConf.ask_verbosity_on_launch && _.has(promptData, 'prompts.verbosity.value.value')) {
            launchData.verbosity = promptData.prompts.verbosity.value.value;
        }
        if (promptData.launchConf.ask_inventory_on_launch && _.has(promptData, 'prompts.inventory.value.id')) {
            launchData.inventory_id = promptData.prompts.inventory.value.id;
        }
        if (promptData.launchConf.ask_credential_on_launch){
            launchData.credentials = [];
            promptData.prompts.credentials.value.forEach((credential) => {
                launchData.credentials.push(credential.id);
            });
        }
        if (promptData.launchConf.ask_diff_mode_on_launch && _.has(promptData, 'prompts.diffMode.value')) {
            launchData.diff_mode = promptData.prompts.diffMode.value;
        }
        if (promptData.launchConf.ask_scm_branch_on_launch && _.has(promptData, 'prompts.scmBranch.value')) {
            launchData.scm_branch = promptData.prompts.scmBranch.value;
        }
        if (promptData.prompts.credentials.passwords) {
            _.forOwn(promptData.prompts.credentials.passwords, (val, key) => {
                if (!launchData.credential_passwords) {
                    launchData.credential_passwords = {};
                }
                if (key === "ssh_key_unlock") {
                    launchData.credential_passwords.ssh_key_unlock = val.value;
                } else if (key !== "vault") {
                    launchData.credential_passwords[`${key}`] = val.value;
                } else {
                    _.each(val, (vaultCred) => {
                        launchData.credential_passwords[vaultCred.vault_id ? `${key}_password.${vaultCred.vault_id}` : `${key}_password`] = vaultCred.value;
                    });
                }
            });
        }

        if (_.get(promptData, 'templateType') === 'workflow_job_template') {
            if (_.get(launchData, 'inventory_id', null) === null) {
                // It's possible to get here on a workflow job template with an inventory prompt and no
                // default value by selecting an inventory, removing it, selecting a different inventory,
                // and then reverting. A null inventory_id may be accepted by the API for prompted workflow
                // inventories in the future, but for now they will 400. As such, we intercept that case here
                // and remove it from the request data prior to launching.
                delete launchData.inventory_id;
            }
        }

        return launchData;
    };

    this.bundlePromptDataForRelaunch = (promptData) => {
        const launchData = {};

        if(promptData.relaunchHostType) {
            launchData.hosts = promptData.relaunchHostType;
        }

        if (promptData.prompts.credentials.passwords) {
            _.forOwn(promptData.prompts.credentials.passwords, (val, key) => {
                if (!launchData.credential_passwords) {
                    launchData.credential_passwords = {};
                }
                if (key === "ssh_key_unlock") {
                    launchData.credential_passwords.ssh_key_unlock = val.value;
                } else if (key !== "vault") {
                    launchData.credential_passwords[`${key}`] = val.value;
                } else {
                    _.each(val, (vaultCred) => {
                        launchData.credential_passwords[vaultCred.vault_id ? `${key}_password.${vaultCred.vault_id}` : `${key}_password`] = vaultCred.value;
                    });
                }
            });
        }

        return launchData;
    };

    this.bundlePromptDataForSaving = (params) => {
        const promptDataToSave = params.dataToSave ? params.dataToSave : {};

        if(params.promptData.launchConf.survey_enabled){
            if(!promptDataToSave.extra_data) {
                promptDataToSave.extra_data = {};
            }
            for (var i=0; i < params.promptData.surveyQuestions.length; i++){
                var fld = params.promptData.surveyQuestions[i].variable;
                // grab all survey questions that have answers
                if(params.promptData.surveyQuestions[i].required || (params.promptData.surveyQuestions[i].required === false && params.promptData.surveyQuestions[i].model.toString()!=="")) {
                    promptDataToSave.extra_data[fld] = params.promptData.surveyQuestions[i].model;
                }

                if(params.promptData.surveyQuestions[i].required === false && _.isEmpty(params.promptData.surveyQuestions[i].model)) {
                    switch (params.promptData.surveyQuestions[i].type) {
                        // for optional text and text-areas, submit a blank string if min length is 0
                        // -- this is confusing, for an explanation see:
                        //    http://docs.ansible.com/ansible-tower/latest/html/userguide/job_templates.html#optional-survey-questions
                        //
                        case "text":
                        case "textarea":
                        if (params.promptData.surveyQuestions[i].min === 0) {
                            promptDataToSave.extra_data[fld] = "";
                        }
                        break;
                    }
                }
            }
        }

        const launchConfDefaults = _.get(params, ['promptData', 'launchConf', 'defaults'], {});

        if(_.has(params, 'promptData.prompts.jobType.value.value') && _.get(params, 'promptData.launchConf.ask_job_type_on_launch')) {
            promptDataToSave.job_type = launchConfDefaults.job_type && launchConfDefaults.job_type === params.promptData.prompts.jobType.value.value ? null : params.promptData.prompts.jobType.value.value;
        }
        if(_.has(params, 'promptData.prompts.tags.value') && _.get(params, 'promptData.launchConf.ask_tags_on_launch')){
            const templateDefaultJobTags = launchConfDefaults.job_tags.split(',');
            promptDataToSave.job_tags = (_.isEqual(templateDefaultJobTags.sort(), params.promptData.prompts.tags.value.map(a => a.value).sort())) ? null : params.promptData.prompts.tags.value.map(a => a.value).join();
        }
        if(_.has(params, 'promptData.prompts.skipTags.value') && _.get(params, 'promptData.launchConf.ask_skip_tags_on_launch')){
            const templateDefaultSkipTags = launchConfDefaults.skip_tags.split(',');
            promptDataToSave.skip_tags = (_.isEqual(templateDefaultSkipTags.sort(), params.promptData.prompts.skipTags.value.map(a => a.value).sort())) ? null : params.promptData.prompts.skipTags.value.map(a => a.value).join();
        }
        if(_.has(params, 'promptData.prompts.limit.value') && _.get(params, 'promptData.launchConf.ask_limit_on_launch')){
            promptDataToSave.limit = launchConfDefaults.limit && launchConfDefaults.limit === params.promptData.prompts.limit.value ? null : params.promptData.prompts.limit.value;
        }
        if(_.has(params, 'promptData.prompts.verbosity.value.value') && _.get(params, 'promptData.launchConf.ask_verbosity_on_launch')){
            promptDataToSave.verbosity = launchConfDefaults.verbosity && launchConfDefaults.verbosity === params.promptData.prompts.verbosity.value.value ? null : params.promptData.prompts.verbosity.value.value;
        }
        if(_.has(params, 'promptData.prompts.inventory.value') && _.get(params, 'promptData.launchConf.ask_inventory_on_launch')){
            promptDataToSave.inventory = launchConfDefaults.inventory && launchConfDefaults.inventory.id === params.promptData.prompts.inventory.value.id ? null : params.promptData.prompts.inventory.value.id;
        }
        if(_.has(params, 'promptData.prompts.diffMode.value') && _.get(params, 'promptData.launchConf.ask_diff_mode_on_launch')){
            promptDataToSave.diff_mode = launchConfDefaults.diff_mode && launchConfDefaults.diff_mode === params.promptData.prompts.diffMode.value ? null : params.promptData.prompts.diffMode.value;
        }
        if(_.has(params, 'promptData.prompts.scmBranch.value') && _.get(params, 'promptData.launchConf.ask_scm_branch_on_launch')){
            promptDataToSave.scm_branch = launchConfDefaults.scm_branch && launchConfDefaults.scm_branch === params.promptData.prompts.scmBranch.value ? null : params.promptData.prompts.scmBranch.value;
        }
        return promptDataToSave;
    };
}

PromptService.$inject = ['Empty', '$filter'];

export default PromptService;
