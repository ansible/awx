export default
    function OwnerChange() {
        return function(params) {
            var scope = params.scope,
            owner = scope.owner;
            if (owner === 'team') {
                scope.team_required = true;
                scope.user_required = false;
                scope.user = null;
                scope.user_username = null;
            } else {
                scope.team_required = false;
                scope.user_required = true;
                scope.team = null;
                scope.team_name = null;
            }
        };
    }
