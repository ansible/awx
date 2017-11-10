import atLibServices from '~services';

import Base from '~models/Base';
import Config from '~models/Config';
import Credential from '~models/Credential';
import CredentialType from '~models/CredentialType';
import Me from '~models/Me';
import Organization from '~models/Organization';
import Project from '~models/Project';
import JobTemplate from '~models/JobTemplate';
import WorkflowJobTemplateNode from '~models/WorkflowJobTemplateNode';
import InventorySource from '~models/InventorySource';
import Inventory from '~models/Inventory';
import InventoryScript from '~models/InventoryScript';

import ModelsStrings from '~models/models.strings';

const MODULE_NAME = 'at.lib.models';

angular
    .module(MODULE_NAME, [
        atLibServices
    ])
    .service('BaseModel', Base)
    .service('ConfigModel', Config)
    .service('CredentialModel', Credential)
    .service('CredentialTypeModel', CredentialType)
    .service('MeModel', Me)
    .service('OrganizationModel', Organization)
    .service('ProjectModel', Project)
    .service('JobTemplateModel', JobTemplate)
    .service('WorkflowJobTemplateNodeModel', WorkflowJobTemplateNode)
    .service('InventorySourceModel', InventorySource)
    .service('InventoryModel', Inventory)
    .service('InventoryScriptModel', InventoryScript)
    .service('ModelsStrings', ModelsStrings);

export default MODULE_NAME;
