function ComponentsStrings (BaseString) {
    BaseString.call(this, 'components');

    let t = this.t;
    let ns = this.components;

    ns.REPLACE = t.s('REPLACE');
    ns.REVERT = t.s('REVERT');
    ns.ENCRYPTED = t.s('ENCRYPTED');
    ns.OPTIONS = t.s('OPTIONS');
    ns.SHOW = t.s('SHOW');
    ns.HIDE = t.s('HIDE');

    ns.message = {
        REQUIRED_INPUT_MISSING: t.s('Please enter a value.'),
        INVALID_INPUT: t.s('Invalid input for this type.')
    };

    ns.form = {
        SUBMISSION_ERROR_TITLE: t.s('Unable to Submit'),
        SUBMISSION_ERROR_MESSAGE:t.s('Unexpected server error. View the console for more information'),
        SUBMISSION_ERROR_PREFACE: t.s('Unexpected Error')
    };

    ns.group = {
        UNSUPPORTED_ERROR_PREFACE: t.s('Unsupported input type')
    };

    ns.label = {
        PROMPT_ON_LAUNCH: t.s('Prompt on launch')
    };

    ns.select = {
        UNSUPPORTED_TYPE_ERROR: t.s('Unsupported display model type'),
        EMPTY_PLACEHOLDER: t.s('NO OPTIONS AVAILABLE')
    };

    ns.textarea = {
        SSH_KEY_HINT: t.s('HINT: Drag and drop an SSH private key file on the field below.')
    };

    ns.lookup = {
        NOT_FOUND: t.s('That value was not found. Please enter or select a valid value.')
    };

    ns.truncate = {
        DEFAULT: t.s('Copy full revision to clipboard.'),
        COPIED: t.s('Copied to clipboard.')
    };

    ns.capacityBar = {
        IS_OFFLINE: t.s('Unavailable to run jobs.')
    };
}

ComponentsStrings.$inject = ['BaseStringService'];

export default ComponentsStrings;
