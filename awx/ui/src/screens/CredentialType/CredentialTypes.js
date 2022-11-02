import React, { useState, useCallback } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';
import PersistentFilters from 'components/PersistentFilters';
import ScreenHeader from 'components/ScreenHeader';
import CredentialTypeAdd from './CredentialTypeAdd';
import CredentialTypeList from './CredentialTypeList';
import CredentialType from './CredentialType';

function CredentialTypes() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/credential_types': t`Credential Types`,
    '/credential_types/add': t`Create new credential type`,
  });

  const buildBreadcrumbConfig = useCallback((credentialTypes) => {
    if (!credentialTypes) {
      return;
    }
    setBreadcrumbConfig({
      '/credential_types': t`Credential Types`,
      '/credential_types/add': t`Create new credential Type`,
      [`/credential_types/${credentialTypes.id}`]: `${credentialTypes.name}`,
      [`/credential_types/${credentialTypes.id}/edit`]: t`Edit details`,
      [`/credential_types/${credentialTypes.id}/details`]: t`Details`,
    });
  }, []);
  return (
    <>
      <ScreenHeader
        streamType="credential_type"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/credential_types/add">
          <CredentialTypeAdd />
        </Route>
        <Route path="/credential_types/:id">
          <CredentialType setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/credential_types">
          <PersistentFilters pageKey="credentialTypes">
            <CredentialTypeList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export default CredentialTypes;
