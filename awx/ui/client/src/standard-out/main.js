/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import stdoutAdhocRoute from './adhoc/standard-out-adhoc.route';
import stdoutManagementJobsRoute from './management-jobs/standard-out-management-jobs.route';
import stdoutInventorySyncRoute from './inventory-sync/standard-out-inventory-sync.route';
import stdoutScmUpdateRoute from './scm-update/standard-out-scm-update.route';
import {JobStdoutController} from './standard-out.controller';
import StandardOutHelper from './standard-out-factories/main';
import standardOutLogDirective from './log/main';

export default angular.module('standardOut', [StandardOutHelper.name, standardOutLogDirective.name])
    .controller('JobStdoutController', JobStdoutController)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(stdoutAdhocRoute);
        $stateExtender.addState(stdoutManagementJobsRoute);
        $stateExtender.addState(stdoutInventorySyncRoute);
        $stateExtender.addState(stdoutScmUpdateRoute);
    }]);
