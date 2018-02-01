import _ from 'lodash';

import actions from './sections/actions';
import breadcrumb from './sections/breadcrumb';
import createFormSection from './sections/createFormSection';
import createTableSection from './sections/createTableSection';
import header from './sections/header';
import lookupModal from './sections/lookupModal';
import navigation from './sections/navigation';
import pagination from './sections/pagination';
import permissions from './sections/permissions';
import search from './sections/search';

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/jobs`;
    },
    sections: {}, // TODO: Fill this out
    elements: {}, // TODO: Fill this out
    commands: [], // TODO: Fill this out as needed
};
