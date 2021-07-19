import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import { useConfig } from 'contexts/Config';
import MiscAuthenticationDetail from './MiscAuthenticationDetail';
import MiscAuthenticationEdit from './MiscAuthenticationEdit';

function MiscAuthentication() {
  const baseURL = '/settings/miscellaneous_authentication';
  const { me } = useConfig();

  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <MiscAuthenticationDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            {me?.is_superuser ? (
              <MiscAuthenticationEdit />
            ) : (
              <Redirect to={`${baseURL}/details`} />
            )}
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>
                {t`View Miscellaneous Authentication settings`}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default MiscAuthentication;
