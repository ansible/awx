import React, { useState, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import CredentialTypeAdd from './CredentialTypeAdd';
import CredentialTypeList from './CredentialTypeList';
import CredentialType from './CredentialType';
import Breadcrumbs from '../../components/Breadcrumbs';

function CredentialTypes({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/credential_types': i18n._(t`Credential Types`),
    '/credential_types/add': i18n._(t`Create new credential type`),
  });

  const buildBreadcrumbConfig = useCallback(
    credentialTypes => {
      if (!credentialTypes) {
        return;
      }
      setBreadcrumbConfig({
        '/credential_types': i18n._(t`Credential Types`),
        '/credential_types/add': i18n._(t`Create new credential Type`),
        [`/credential_types/${credentialTypes.id}`]: `${credentialTypes.name}`,
        [`/credential_types/${credentialTypes.id}/edit`]: i18n._(
          t`Edit details`
        ),
        [`/credential_types/${credentialTypes.id}/details`]: i18n._(t`Details`),
      });
    },
    [i18n]
  );
  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/credential_types/add">
          <CredentialTypeAdd />
        </Route>
        <Route path="/credential_types/:id">
          <CredentialType setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/credential_types">
          <CredentialTypeList />
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(CredentialTypes);
