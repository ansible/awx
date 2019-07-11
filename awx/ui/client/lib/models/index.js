import atLibServices from '~services';

import AdHocCommand from '~models/AdHocCommand';
import Application from '~models/Application';
import Base from '~models/Base';
import Config from '~models/Config';
import Credential from '~models/Credential';
import CredentialType from '~models/CredentialType';
import Instance from '~models/Instance';
import InstanceGroup from '~models/InstanceGroup';
import Inventory from '~models/Inventory';
import InventoryScript from '~models/InventoryScript';
import InventorySource from '~models/InventorySource';
import InventoryUpdate from '~models/InventoryUpdate';
import Job from '~models/Job';
import JobEvent from '~models/JobEvent';
import JobTemplate from '~models/JobTemplate';
import Me from '~models/Me';
import NotificationTemplate from '~models/NotificationTemplate';
import Organization from '~models/Organization';
import Project from '~models/Project';
import ProjectUpdate from '~models/ProjectUpdate';
import Schedule from '~models/Schedule';
import SystemJob from '~models/SystemJob';
import Token from '~models/Token';
import UnifiedJob from '~models/UnifiedJob';
import UnifiedJobTemplate from '~models/UnifiedJobTemplate';
import User from '~models/User';
import WorkflowJob from '~models/WorkflowJob';
import WorkflowJobTemplate from '~models/WorkflowJobTemplate';
import WorkflowJobTemplateNode from '~models/WorkflowJobTemplateNode';

import ModelsStrings from '~models/models.strings';

const MODULE_NAME = 'at.lib.models';

angular
    .module(MODULE_NAME, [
        atLibServices
    ])
    .service('AdHocCommandModel', AdHocCommand)
    .service('ApplicationModel', Application)
    .service('BaseModel', Base)
    .service('ConfigModel', Config)
    .service('CredentialModel', Credential)
    .service('CredentialTypeModel', CredentialType)
    .service('InstanceGroupModel', InstanceGroup)
    .service('InstanceModel', Instance)
    .service('InventoryModel', Inventory)
    .service('InventoryScriptModel', InventoryScript)
    .service('InventorySourceModel', InventorySource)
    .service('InventoryUpdateModel', InventoryUpdate)
    .service('JobEventModel', JobEvent)
    .service('JobModel', Job)
    .service('JobTemplateModel', JobTemplate)
    .service('MeModel', Me)
    .service('ModelsStrings', ModelsStrings)
    .service('NotificationTemplate', NotificationTemplate)
    .service('OrganizationModel', Organization)
    .service('ProjectModel', Project)
    .service('ProjectUpdateModel', ProjectUpdate)
    .service('ScheduleModel', Schedule)
    .service('SystemJobModel', SystemJob)
    .service('TokenModel', Token)
    .service('UnifiedJobModel', UnifiedJob)
    .service('UnifiedJobTemplateModel', UnifiedJobTemplate)
    .service('UserModel', User)
    .service('WorkflowJobModel', WorkflowJob)
    .service('WorkflowJobTemplateModel', WorkflowJobTemplate)
    .service('WorkflowJobTemplateNodeModel', WorkflowJobTemplateNode);

export default MODULE_NAME;
