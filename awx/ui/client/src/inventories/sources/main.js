/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import sourcesList from './list/main';
import sourcesAdd from './add/main';
import sourcesEdit from './edit/main';
import sourcesFormDefinition from './sources.form';
import sourcesListDefinition from './sources.list';
import service from './sources.service';

export default
    angular.module('sources', [
        sourcesList.name,
        sourcesAdd.name,
        sourcesEdit.name
    ])
    .value('SourcesFormDefinition', sourcesFormDefinition)
    .value('SourcesListDefinition', sourcesListDefinition)
    .service('SourcesService', service);
