import {templateUrl} from '../shared/template-url/template-url.factory';
import {PortalModeJobTemplatesController} from './portal-mode-job-templates.controller';
import {PortalModeJobsController} from './portal-mode-jobs.controller';

// Using multiple named views requires a parent layout
// https://github.com/angular-ui/ui-router/wiki/Multiple-Named-Views
export default {
	name: 'portalMode',
    url: '/portal',
    ncyBreadcrumb: {
        label: "MY VIEW"
    },
    views: {
        // the empty parent ui-view
        "" : {
            templateUrl: templateUrl('portal-mode/portal-mode-layout'),
        },
        // named ui-views inside the above
        'job-templates@portalMode': {
            templateUrl: templateUrl('portal-mode/portal-mode-job-templates'),
            controller: PortalModeJobTemplatesController
        },
        'jobs@portalMode': {
            templateUrl: templateUrl('portal-mode/portal-mode-jobs'),
            controller: PortalModeJobsController
        }
    }
};
