export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: false,
                templateUrl: templateUrl('credentials/ownerList'),
                link: function(scope) {
                    scope.owners_list = scope.credential.summary_fields.owners && scope.credential.summary_fields.owners.length > 0 ? scope.credential.summary_fields.owners : [];
                }
            };
        }
    ];
