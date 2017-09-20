import Base from '~models/Base';
import Config from '~models/Config';
import Credential from '~models/Credential';
import CredentialType from '~models/CredentialType';
import Me from '~models/Me';
import Organization from '~models/Organization';

angular
    .module('at.lib.models', [])
    .service('BaseModel', Base)
    .service('ConfigModel', Config)
    .service('CredentialModel', Credential)
    .service('CredentialTypeModel', CredentialType)
    .service('MeModel', Me)
    .service('OrganizationModel', Organization);
