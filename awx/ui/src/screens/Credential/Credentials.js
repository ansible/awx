import React, { useState, useCallback } from 'react';
import { Route, Switch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Config } from 'contexts/Config';
import ScreenHeader from 'components/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import Credential from './Credential';
import CredentialAdd from './CredentialAdd';
import { CredentialList } from './CredentialList';

function Credentials() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/credentials': t`Credentials`,
    '/credentials/add': t`Create New Credential`,
  });

  const buildBreadcrumbConfig = useCallback((credential) => {
    if (!credential) {
      return;
    }

    setBreadcrumbConfig({
      '/credentials': t`Credentials`,
      '/credentials/add': t`Create New Credential`,
      [`/credentials/${credential.id}`]: `${credential.name}`,
      [`/credentials/${credential.id}/edit`]: t`Edit Details`,
      [`/credentials/${credential.id}/details`]: t`Details`,
      [`/credentials/${credential.id}/access`]: t`Access`,
      [`/credentials/${credential.id}/job_templates`]: t`Job Templates`,
    });
  }, []);

  return (
    <>
      <ScreenHeader
        streamType="credential"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/credentials/add">
          <Config>{({ me }) => <CredentialAdd me={me || {}} />}</Config>
        </Route>
        <Route path="/credentials/:id">
          <Credential setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/credentials">
          <PersistentFilters pageKey="credentials">
            <CredentialList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export default Credentials;
