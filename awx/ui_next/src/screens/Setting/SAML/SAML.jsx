import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import SAMLDetail from './SAMLDetail';
import SAMLEdit from './SAMLEdit';

function SAML({ i18n }) {
  const baseUrl = '/settings/saml';

  return (
    <PageSection>
      <Card>
        {i18n._(t`SAML settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <SAMLDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <SAMLEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(SAML);
