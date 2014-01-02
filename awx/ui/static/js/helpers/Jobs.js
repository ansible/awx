/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobsHelper
 *
 *  Routines shared by job related controllers
 *  
 */

angular.module('JobsHelper', [ ])
    .factory('JobStatusToolTip', [ function() {
    return function(status) {
        var toolTip;
        switch (status) {
            case 'successful':
            case 'success':
                toolTip = 'There were no failed tasks.';
                break;
            case 'failed':
                toolTip = 'Some tasks encountered errors.';
                break; 
            case 'canceled': 
                toolTip = 'Stopped by user request.';
                break;
            case 'new':
                toolTip = 'In queue, waiting on task manager.';
                break;
            case 'waiting':
                toolTip = 'SCM Update or Inventory Update is executing.';
                break;
            case 'pending':
                toolTip = 'Not in queue, waiting on task manager.';
                break;
            case 'running':
                toolTip = 'Playbook tasks executing.';
                break;
        }
        return toolTip;
        }
        }]);