import Base from './Base';
import Config from './Config';
import Credential from './Credential';
import CredentialType from './CredentialType';
import Me from './Me';
import Organization from './Organization';

angular
    .module('at.lib.models', [])
    .service('BaseModel', Base)
    .service('ConfigModel', Config)
    .service('CredentialModel', Credential)
    .service('CredentialTypeModel', CredentialType)
    .service('MeModel', Me)
    .service('OrganizationModel', Organization);
