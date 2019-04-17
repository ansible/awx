/*************************************************
* Copyright (c) 2015 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors',
    function ($rootScope, Rest, GetBasePath, ProcessErrors) {
        return {          
            updateInsightsTrackingState: function(tracking_type) {
                if (tracking_type === true || tracking_type === false) {
                        Rest.setUrl(`${GetBasePath('settings')}system`);
                        Rest.patch({ INSIGHTS_TRACKING_STATE: tracking_type })
                            .catch(function ({data, status}) {
                                ProcessErrors($rootScope, data, status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to patch INSIGHTS_TRACKING_STATE in settings: ' +
                                        status });
                            });
                } else {
                    throw new Error(`Can't update insights data enabled in settings to
                        "${tracking_type}"`);
                }
            }
        };
    }];
