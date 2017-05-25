const REQUIRED_INPUT_MISSING_MESSAGE = 'Please enter a value.';
const DEFAULT_INVALID_INPUT_MESSAGE = 'Invalid input for this type.';

function BaseInputController () {
    return function extend (type, scope, element, form) {
        let vm = this;

        scope.state = scope.state || {};

        scope.state._required = scope.state.required || false;
        scope.state._isValid = scope.state.isValid || false;
        scope.state._disabled = scope.state.disabled || false;

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
    };
}

export default BaseInputController;
