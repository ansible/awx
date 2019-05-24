/*************************************************
* Copyright (c) 2015 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', 'i18n',
    function ($rootScope, Rest, GetBasePath, ProcessErrors, i18n) {
        return {
            updateInsightsTrackingState: function(tracking_state) {
                var schedulesUrl = `${GetBasePath('schedules')}?unified_job_template__name=Automation%20Insights%20Collection`;
                var deferredPatchArr = [];
                Rest.setUrl(schedulesUrl);
                Rest.get()
                    .then((data) => {
                        data.data.results.forEach(obj => {
                            const scheduleToPatchUrl =`${GetBasePath('schedules')}${obj.id}`;
                            Rest.setUrl(scheduleToPatchUrl);
                            deferredPatchArr.push(Rest.patch({ "enabled": tracking_state }));
                        });
                        Promise.all(deferredPatchArr)
                            .catch(function ({data, status}) {
                                ProcessErrors($rootScope, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to patch INSIGHTS_TRACKING_STATE in settings: ') +
                                                    status + data});
                               });
                    });
            }
        };
    }];
