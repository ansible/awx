import {templateUrl} from '../shared/template-url/template-url.factory';
import controller from './setup.controller';

export default {
    name: 'setup',
    route: '/setup',
    controller: controller,
    templateUrl: templateUrl('setup-menu/setup-menu')
};
