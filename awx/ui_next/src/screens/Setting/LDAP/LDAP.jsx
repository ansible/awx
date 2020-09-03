import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import LDAPDetail from './LDAPDetail';
import LDAPEdit from './LDAPEdit';

function LDAP({ i18n }) {
  const baseUrl = '/settings/ldap';

  return (
    <PageSection>
      <Card>
        {i18n._(t`LDAP settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <LDAPDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <LDAPEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(LDAP);
