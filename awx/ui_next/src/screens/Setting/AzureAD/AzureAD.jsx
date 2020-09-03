import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import AzureADDetail from './AzureADDetail';
import AzureADEdit from './AzureADEdit';

function AzureAD({ i18n }) {
  const baseUrl = '/settings/azure';

  return (
    <PageSection>
      <Card>
        {i18n._(t`Azure AD settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <AzureADDetail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <AzureADEdit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(AzureAD);
