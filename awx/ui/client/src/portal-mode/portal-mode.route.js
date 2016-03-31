import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
	name: 'portalMode',
    url: '/portal',
    templateUrl: templateUrl('portal-mode/portal-mode'),
    controller: 'PortalModeController',
    ncyBreadcrumb: {
        label: "PORTAL MODE"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
}