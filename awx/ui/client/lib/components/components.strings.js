function ComponentsStrings (BaseString) {
    BaseString.call(this, 'components');
    
    let t = this.t;
    let ns = this.components;

    ns.REPLACE = t('REPLACE');
    ns.REVERT = t('REVERT');
    ns.ENCRYPTED = t('ENCRYPTED');
    ns.OPTIONS = t('OPTIONS');
    ns.SHOW = t('SHOW');
    ns.HIDE = t('HIDE');

    ns.message = {
        REQUIRED_INPUT_MISSING: t('Please enter a value.'),
        INVALID_INPUT: t('Invalid input for this type.')
    };

    ns.form = {
        SUBMISSION_ERROR_TITLE: t('Unable to Submit'),
        SUBMISSION_ERROR_MESSAGE:t('Unexpected server error. View the console for more information'),
        SUBMISSION_ERROR_PREFACE: t('Unexpected Error')
    };

    ns.group = {
        UNSUPPORTED_ERROR_PREFACE: t('Unsupported input type')
    };

    ns.label = {
        PROMPT_ON_LAUNCH: t('Prompt on launch')
    };

    ns.select = {
        UNSUPPORTED_TYPE_ERROR: t('Unsupported display model type'),
        EMPTY_PLACEHOLDER: t('NO OPTIONS AVAILABLE')
    };

    ns.textarea = {
        SSH_KEY_HINT: t('HINT: Drag and drop an SSH private key file on the field below.')
    };

    ns.lookup = {
        NOT_FOUND: t('That value was not found. Please enter or select a valid value.')
    };
}

ComponentsStrings.$inject = ['BaseStringService'];

export default ComponentsStrings;
