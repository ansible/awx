import {templateUrl} from '../shared/template-url/template-url.factory';
import controller from './about.controller';

export default {
    name: 'setup.about',
    route: '/about',
    controller: controller,
    ncyBreadcrumb: {
        label: "ABOUT"
    },
    onExit: function(){
        // hacky way to handle user browsing away via URL bar
        $('.modal-backdrop').remove();
        $('body').removeClass('modal-open');
    },
    templateUrl: templateUrl('about/about')
};
