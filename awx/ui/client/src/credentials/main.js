/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import ownerList from './ownerList.directive';
import CredentialsList from './list/credentials-list.controller';
import BecomeMethodChange from './factories/become-method-change.factory';
import CredentialFormSave from './factories/credential-form-save.factory';
import KindChange from './factories/kind-change.factory';
import OwnerChange from './factories/owner-change.factory';
import CredentialList from './credentials.list';
import CredentialForm from './credentials.form';

export default
    angular.module('credentials', [])
        .directive('ownerList', ownerList)
        .factory('BecomeMethodChange', BecomeMethodChange)
        .factory('CredentialFormSave', CredentialFormSave)
        .factory('KindChange', KindChange)
        .factory('OwnerChange', OwnerChange)
        .controller('CredentialsList', CredentialsList)
        .factory('CredentialList', CredentialList)
        .factory('CredentialForm', CredentialForm);
