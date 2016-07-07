import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'setup',
    route: '/setup',
    ncyBreadcrumb: {
        label: "SETUP"
    },
    templateUrl: templateUrl('setup-menu/setup-menu')
};
