/* jshint unused: vars */

export default
    [   function() {
            return  {   restrict: 'E',
                        templateUrl: '/static/js/system-tracking/fact-data-table/fact-data-table.partial.html',
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
