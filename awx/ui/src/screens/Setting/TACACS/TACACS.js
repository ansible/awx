import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';

import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import TACACSDetail from './TACACSDetail';
import TACACSEdit from './TACACSEdit';

function TACACS() {
  const baseURL = '/settings/tacacs';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <TACACSDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <TACACSEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>{t`View TACACS+ settings`}</Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default TACACS;
