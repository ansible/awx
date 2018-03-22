import atLibServices from '~services';

import Application from '~models/Application';
import AdHocCommand from '~models/AdHocCommand';
import Base from '~models/Base';
import Config from '~models/Config';
import Credential from '~models/Credential';
import CredentialType from '~models/CredentialType';
import Instance from '~models/Instance';
import InstanceGroup from '~models/InstanceGroup';
import Inventory from '~models/Inventory';
import InventoryScript from '~models/InventoryScript';
import InventorySource from '~models/InventorySource';
import Job from '~models/Job';
import JobTemplate from '~models/JobTemplate';
import Me from '~models/Me';
import ModelsStrings from '~models/models.strings';
import NotificationTemplate from '~models/NotificationTemplate';
import Organization from '~models/Organization';
import Project from '~models/Project';
import Schedule from '~models/Schedule';
import UnifiedJobTemplate from '~models/UnifiedJobTemplate';
import WorkflowJob from '~models/WorkflowJob';
import WorkflowJobTemplate from '~models/WorkflowJobTemplate';
import WorkflowJobTemplateNode from '~models/WorkflowJobTemplateNode';
import UnifiedJob from '~models/UnifiedJob';

const MODULE_NAME = 'at.lib.models';

angular
    .module(MODULE_NAME, [
        atLibServices
    ])
    .service('ApplicationModel', Application)
    .service('AdHocCommandModel', AdHocCommand)
    .service('BaseModel', Base)
    .service('ConfigModel', Config)
    .service('CredentialModel', Credential)
    .service('CredentialTypeModel', CredentialType)
    .service('InstanceGroupModel', InstanceGroup)
    .service('InstanceModel', Instance)
    .service('InventoryModel', Inventory)
    .service('InventoryScriptModel', InventoryScript)
    .service('InventorySourceModel', InventorySource)
    .service('JobModel', Job)
    .service('JobTemplateModel', JobTemplate)
    .service('MeModel', Me)
    .service('ModelsStrings', ModelsStrings)
    .service('NotificationTemplate', NotificationTemplate)
    .service('OrganizationModel', Organization)
    .service('ProjectModel', Project)
    .service('ScheduleModel', Schedule)
    .service('UnifiedJobModel', UnifiedJob)
    .service('UnifiedJobTemplateModel', UnifiedJobTemplate)
    .service('WorkflowJobModel', WorkflowJob)
    .service('WorkflowJobTemplateModel', WorkflowJobTemplate)
    .service('WorkflowJobTemplateNodeModel', WorkflowJobTemplateNode);

export default MODULE_NAME;
