import TemplatesStrings from './templates.strings';
import ListController from './list-templates.controller';

const MODULE_NAME = 'at.features.templates';

angular
    .module(MODULE_NAME, [])
    .controller('ListController', ListController)
    .service('TemplatesStrings', TemplatesStrings);

export default MODULE_NAME;
