import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import AzureADDetail from './AzureADDetail';
import AzureADEdit from './AzureADEdit';

function AzureAD({ i18n }) {
  const baseURL = '/settings/azure';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <AzureADDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <AzureADEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>
                {i18n._(t`View Azure AD settings`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(AzureAD);
