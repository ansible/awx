import React, { useState, useCallback } from 'react';
import { Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs';
import Credential from './Credential';
import CredentialAdd from './CredentialAdd';
import { CredentialList } from './CredentialList';

function Credentials({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/credentials': i18n._(t`Credentials`),
    '/credentials/add': i18n._(t`Create New Credential`),
  });

  const buildBreadcrumbConfig = useCallback(
    credential => {
      if (!credential) {
        return;
      }

      setBreadcrumbConfig({
        '/credentials': i18n._(t`Credentials`),
        '/credentials/add': i18n._(t`Create New Credential`),
        [`/credentials/${credential.id}`]: `${credential.name}`,
        [`/credentials/${credential.id}/edit`]: i18n._(t`Edit Details`),
        [`/credentials/${credential.id}/details`]: i18n._(t`Details`),
        [`/credentials/${credential.id}/access`]: i18n._(t`Access`),
      });
    },
    [i18n]
  );

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/credentials/add">
          <Config>{({ me }) => <CredentialAdd me={me || {}} />}</Config>
        </Route>
        <Route path="/credentials/:id">
          <Credential setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/credentials">
          <CredentialList />
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(Credentials);
