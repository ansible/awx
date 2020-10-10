import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import LoggingDetail from './LoggingDetail';
import LoggingEdit from './LoggingEdit';

function Logging({ i18n }) {
  const baseURL = '/settings/logging';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <LoggingDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <LoggingEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}`}>{i18n._(t`View Logging settings`)}</Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(Logging);
