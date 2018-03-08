function PromptService (Empty, $filter)  {

    this.processPromptValues = (params) => {
        let prompts = {
            credentials: {},
            inventory: {},
            variables: {},
            verbosity: {},
            jobType: {},
            limit: {},
            tags: {},
            skipTags: {},
            diffMode: {}
        };

        prompts.credentials.value = _.has(params, 'launchConf.defaults.credentials') ? _.cloneDeep(params.launchConf.defaults.credentials) : [];
        prompts.inventory.value = _.has(params, 'currentValues.summary_fields.inventory') ? params.currentValues.summary_fields.inventory : (_.has(params, 'launchConf.defaults.inventory') ? params.launchConf.defaults.inventory : null);

        let skipTags = _.has(params, 'currentValues.skip_tags') && params.currentValues.skip_tags ? params.currentValues.skip_tags : (_.has(params, 'launchConf.defaults.skip_tags') ? params.launchConf.defaults.skip_tags : "");
        let jobTags = _.has(params, 'currentValues.job_tags') && params.currentValues.job_tags ? params.currentValues.job_tags : (_.has(params, 'launchConf.defaults.job_tags') ? params.launchConf.defaults.job_tags : "");

        prompts.variables.value = _.has(params, 'launchConf.defaults.extra_vars') && params.launchConf.defaults.extra_vars !== "" ? params.launchConf.defaults.extra_vars : "---";
        prompts.verbosity.choices = _.get(params, 'launchOptions.actions.POST.verbosity.choices', []).map(c => ({label: c[1], value: c[0]}));
        prompts.verbosity.value = _.has(params, 'currentValues.verbosity') && params.currentValues.verbosity ? _.find(prompts.verbosity.choices, item => item.value === params.currentValues.verbosity) : _.find(prompts.verbosity.choices, item => item.value === params.launchConf.defaults.verbosity);
        prompts.jobType.choices = _.get(params, 'launchOptions.actions.POST.job_type.choices', []).map(c => ({label: c[1], value: c[0]}));
        prompts.jobType.value = _.has(params, 'currentValues.job_type') && params.currentValues.job_type ? _.find(prompts.jobType.choices, item => item.value === params.currentValues.job_type) : _.find(prompts.jobType.choices, item => item.value === params.launchConf.defaults.job_type);
        prompts.limit.value = _.has(params, 'currentValues.limit') && params.currentValues.limit ? params.currentValues.limit : (_.has(params, 'launchConf.defaults.limit') ? params.launchConf.defaults.limit : "");
        prompts.tags.options = prompts.tags.value = (jobTags && jobTags !== "") ? jobTags.split(',').map((i) => ({name: i, label: i, value: i})) : [];
        prompts.skipTags.options = prompts.skipTags.value = (skipTags && skipTags !== "") ? skipTags.split(',').map((i) => ({name: i, label: i, value: i})) : [];
        prompts.diffMode.value = _.has(params, 'currentValues.diff_mode') && typeof params.currentValues.diff_mode === 'boolean' ? params.currentValues.diff_mode : (_.has(params, 'launchConf.defaults.diff_mode') ? params.launchConf.defaults.diff_mode : false);

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
                question.choices = question.choices.split(/\n/);
            }
            else if(question.type === "multiplechoice") {
                if(params.extra_data && params.extra_data[question.variable]) {
                    question.model = params.extra_data[question.variable];
                    delete params.extra_data[question.variable];
                } else {
                    question.model = question.default ? angular.copy(question.default) : "";
                }

                question.choices = question.choices.split(/\n/);

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
}

PromptService.$inject = ['Empty', '$filter'];

export default PromptService;
