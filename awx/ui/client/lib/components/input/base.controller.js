function BaseInputController () {
    return function extend (type, scope, form) {
        let vm = this;

        scope.state = scope.state || {};

        scope.state.required = scope.state.required || false;
        scope.state.isValid = scope.state.isValid || false;
        scope.state.disabled = scope.state.disabled || false;

        form.use(type, scope);

        vm.validate = () => {
            let isValid = true;

            if (scope.state.required && !scope.state.value) {
                isValid = false;    
            }

            if (scope.state.validate && !scope.state.validate(scope.state.value)) {
                isValid = false;  
            }

            return isValid;
        };

        vm.check = () => {
            let isValid = vm.validate();

            if (isValid !== scope.state.isValid) {
                scope.state.isValid = isValid;
                form.check();
            }
        };
    };
}

export default BaseInputController;
