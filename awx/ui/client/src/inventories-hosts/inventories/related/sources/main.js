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
import GetSyncStatusMsg from './factories/get-sync-status-msg.factory';
import ViewUpdateStatus from './factories/view-update-status.factory';
import CancelSourceUpdate from './factories/cancel-source-update.factory';
import GetSourceTypeOptions from './factories/get-source-type-options.factory';

export default
    angular.module('sources', [
        sourcesList.name,
        sourcesAdd.name,
        sourcesEdit.name
    ])
    .factory('SourcesFormDefinition', sourcesFormDefinition)
    .factory('SourcesListDefinition', sourcesListDefinition)
    .factory('GetSyncStatusMsg', GetSyncStatusMsg)
    .factory('ViewUpdateStatus', ViewUpdateStatus)
    .factory('CancelSourceUpdate', CancelSourceUpdate)
    .factory('GetSourceTypeOptions', GetSourceTypeOptions)
    .service('SourcesService', service);
