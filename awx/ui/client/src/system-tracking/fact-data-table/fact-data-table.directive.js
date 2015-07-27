/* jshint unused: vars */

export default
    [   'templateUrl',
        function(templateUrl) {
            return  {   restrict: 'E',
                        templateUrl: templateUrl('system-tracking/fact-data-table/fact-data-table'),
                        scope:
                            {   leftHostname: '=',
                                rightHostname: '=',
                                leftScanDate: '=',
                                rightScanDate: '=',
                                leftDataNoScans: '=',
                                rightDataNoScans: '=',
                                isNestedDisplay: '=',
                                singleResultView: '=',
                                factData: '='
                            }
                    };
        }
    ];
