/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import {N_} from "../../i18n";

export default {
    name: 'managementJobsList',
    route: '/management_jobs',
    templateUrl: templateUrl('management-jobs/card/card'),
    controller: 'managementJobsCardController',
    data: {
        activityStream: false,
    },
    ncyBreadcrumb: {
        label: N_('MANAGEMENT JOBS')
    },
};
