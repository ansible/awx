import atLibServices from '~services';

import Base from '~models/Base';
import Config from '~models/Config';
import Credential from '~models/Credential';
import CredentialType from '~models/CredentialType';
import Me from '~models/Me';
import Organization from '~models/Organization';

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
    .service('OrganizationModel', Organization);

export default MODULE_NAME;
