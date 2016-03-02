import {templateUrl} from '../shared/template-url/template-url.factory';
import controller from './about.controller';

export default {
    name: 'setup.about',
    route: '/about',
    controller: controller,
    ncyBreadcrumb: {
        label: "ABOUT"
    },
    templateUrl: templateUrl('about/about')
};
