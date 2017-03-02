export default
    function md5Setup(md5) {
        return function(params) {
            var scope = params.scope,
                master = params.master,
                check_field = params.check_field,
                default_val = params.default_val;

            scope[check_field] = default_val;
            master[check_field] = default_val;

            scope.genMD5 = function (fld) {
                var now = new Date();
                scope[fld] = md5.createHash('AnsibleWorks' + now.getTime());
                scope.$emit('NewMD5Generated');
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

md5Setup.$inject = [   'md5'   ];
