function BaseInputController (strings) {
    // Default values are universal. Don't translate.
    const PROMPT_ON_LAUNCH_VALUE = 'ASK';
    const ENCRYPTED_VALUE = '$encrypted$';

    return function extend (type, scope, element, form) {
        const vm = this;

        vm.strings = strings;

        scope.state = scope.state || {};

        scope.state._touched = false;
        scope.state._required = scope.state.required || false;

        if (scope.state.type === 'boolean') {
            scope.state._isValid = scope.state._isValid || true;
        } else {
            scope.state._isValid = scope.state._isValid || false;
        }

        scope.state._disabled = scope.state._disabled || false;
        scope.state._activeModel = scope.state._activeModel || '_value';

        if (scope.state.ask_at_runtime) {
            scope.state._displayPromptOnLaunch = true;
        }

        if (typeof scope.state._value !== 'undefined') {
            scope.state._edit = true;
            scope.state._preEditValue = scope.state._value;

            if (scope.state._value === PROMPT_ON_LAUNCH_VALUE) {
                scope.state._promptOnLaunch = true;
                scope.state._disabled = true;
                scope.state._activeModel = '_displayValue';
            }

            if (scope.state._value === ENCRYPTED_VALUE) {
                scope.state._displayRevertReplace = true;
                scope.state._enableToggle = true;
                scope.state._disabled = true;
                scope.state._isBeingReplaced = false;
                scope.state._activeModel = '_displayValue';
            }
        } else if (typeof scope.state.default !== 'undefined') {
            scope.state._value = scope.state.default;
        }

        form.register(type, scope);

        if (scope.form && scope.form.disabled) {
            scope.state._enableToggle = false;
        }

        vm.validate = () => {
            let isValid = true;
            let message = '';

            if (scope.state.asTag) {
                return (isValid, message);
            }

            if (scope.state._value || scope.state._displayValue) {
                scope.state._touched = true;
            }

            if (scope.state.type === 'boolean') {
                return { isValid, message };
            }

            if (scope.state._required && (!scope.state._value || !scope.state._value[0]) &&
                !scope.state._displayValue) {
                isValid = false;
                message = vm.strings.get('message.REQUIRED_INPUT_MISSING');
            } else if (scope.state._validate) {
                const result = scope.state._validate(scope.state._value);

                if (!result.isValid) {
                    isValid = false;
                    message = result.message || vm.strings.get('message.INVALID_INPUT');
                }
            }

            return {
                isValid,
                message
            };
        };

        vm.updateValidationState = result => {
            if (!scope.state._touched && scope.state._required) {
                return;
            }

            scope.state._rejected = !result.isValid;
            scope.state._isValid = result.isValid;
            scope.state._message = result.message;

            form.check();
        };

        vm.check = result => {
            result = result || vm.validate();

            vm.updateValidationState(result);
        };

        vm.onRevertReplaceToggle = () => {
            if (!scope.state._isBeingReplaced) {
                scope.state._buttonText = vm.strings.get('REPLACE');
                scope.state._disabled = true;
                scope.state._enableToggle = true;
                scope.state._value = scope.state._preEditValue;
                scope.state._activeModel = '_displayValue';
                scope.state._placeholder = vm.strings.get('ENCRYPTED');
                vm.check();
            } else {
                scope.state._buttonText = vm.strings.get('REVERT');
                scope.state._disabled = false;
                scope.state._enableToggle = false;
                scope.state._activeModel = '_value';
                scope.state._value = '';
                scope.state._placeholder = '';
                vm.check();
            }
            if (scope.form && scope.form.disabled) {
                scope.state._enableToggle = false;
            }
        };

        vm.togglePromptOnLaunch = () => {
            if (scope.state._promptOnLaunch) {
                scope.state._value = PROMPT_ON_LAUNCH_VALUE;
                scope.state._activeModel = '_displayValue';
                scope.state._disabled = true;
                scope.state._enableToggle = false;
            } else if (scope.state._isBeingReplaced === false) {
                scope.state._disabled = true;
                scope.state._enableToggle = true;
                scope.state._value = scope.state._preEditValue;
            } else {
                scope.state._activeModel = '_value';
                scope.state._disabled = false;
                scope.state._value = '';
            }

            vm.check();
        };
    };
}

BaseInputController.$inject = ['ComponentsStrings'];

export default BaseInputController;
