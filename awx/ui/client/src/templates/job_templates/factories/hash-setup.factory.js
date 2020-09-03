export default
    function hashSetup() {
        return function(params) {
            var scope = params.scope,
                main = params.main,
                check_field = params.check_field,
                default_val = params.default_val;

            scope[check_field] = default_val;
            main[check_field] = default_val;

            // Original gist here: https://gist.github.com/jed/982883
            scope.genHash = function (fld) {
                scope[fld] = ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
                    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
                );
                scope.$emit('NewHashGenerated');
            };

            scope.toggleCallback = function (fld) {
                if (scope.allow_callbacks === false) {
                    scope[fld] = '';
                }
            };

            scope.selectAll = function (fld) {
                $('input[name="' + fld + '"]').focus().select();
            };
        };
    }
