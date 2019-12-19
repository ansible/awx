import React from 'react';
import { Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';
import { CredentialList } from './CredentialList';
import CredentialAdd from './CredentialAdd';

function Credentials({ i18n }) {
  const breadcrumbConfig = {
    '/credentials': i18n._(t`Credentials`),
    '/credentials/add': i18n._(t`Create New Credential`),
  };

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/credentials/add" render={() => <CredentialAdd />} />
        <Route path="/credentials" render={() => <CredentialList />} />
      </Switch>
    </>
  );
}

export default withI18n()(Credentials);
