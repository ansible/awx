const REQUIRED_INPUT_MISSING_MESSAGE = 'Please enter a value.';
const DEFAULT_INVALID_INPUT_MESSAGE = 'Invalid input for this type.';
const PROMPT_ON_LAUNCH_VALUE = 'ASK';
const ENCRYPTED_VALUE = '$encrypted$';

function BaseInputController () {
    return function extend (type, scope, element, form) {
        let vm = this;

        scope.state = scope.state || {};

        scope.state._required = scope.state.required || false;
        scope.state._isValid = scope.state.isValid || false;
        scope.state._disabled = scope.state.disabled || false;
        scope.state._activeModel = '_value';

        if (scope.state.ask_at_runtime) {
            scope.state._displayPromptOnLaunch = true;
        }

        if (scope.state._value) {
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
        }

        form.register(type, scope);

        vm.validate = () => {
            let isValid = true;
            let message = '';

            if (scope.state._required && !scope.state._value) {
                isValid = false;    
                message = REQUIRED_INPUT_MISSING_MESSAGE;
            }

            if (scope.state.validate) {
                let result = scope.state._validate(scope.state._value);

                if (!result.isValid) {
                    isValid = false;
                    message = result.message || DEFAULT_INVALID_INPUT_MESSAGE;
                }
            }

            return {
                isValid,
                message
            };
        };

        vm.check = () => {
            let result = vm.validate();

            if (result.isValid !== scope.state._isValid) {
                scope.state._rejected = !result.isValid;
                scope.state._isValid = result.isValid;
                scope.state._message = result.message;

                form.check();
            }
        };

        vm.toggleRevertReplace = () => {
            scope.state._isBeingReplaced = !scope.state._isBeingReplaced;

            if (!scope.state._isBeingReplaced) {
                scope.state._buttonText = 'REPLACE';
                scope.state._disabled = true;
                scope.state._enableToggle = true;
                scope.state._value = scope.state._preEditValue;
                scope.state._activeModel = '_displayValue';
                scope.state._placeholder = 'ENCRYPTED';
            } else {
                scope.state._buttonText = 'REVERT';
                scope.state._disabled = false;
                scope.state._enableToggle = false;
                scope.state._activeModel = '_value';
                scope.state._value = '';
                scope.state._placeholder = '';
            }
        };

        vm.togglePromptOnLaunch = () => {
            if (scope.state._promptOnLaunch) {
                scope.state._value = PROMPT_ON_LAUNCH_VALUE;
                scope.state._activeModel = '_displayValue';
                scope.state._disabled = true;
                scope.state._enableToggle = false;
            } else {
                if (scope.state._isBeingReplaced === false) {
                    scope.state._disabled = true;
                    scope.state._enableToggle = true;
                    scope.state._value = scope.state._preEditValue;
                } else {
                    scope.state._activeModel = '_value';
                    scope.state._disabled = false;
                    scope.state._value = ''; 
                }
            }
            
            vm.check();
        };
    };
}

export default BaseInputController;
