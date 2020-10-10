import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import MiscSystemDetail from './MiscSystemDetail';
import MiscSystemEdit from './MiscSystemEdit';

function MiscSystem({ i18n }) {
  const baseURL = '/settings/miscellaneous_system';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <MiscSystemDetail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <MiscSystemEdit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>
                {i18n._(t`View Miscellaneous System settings`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(MiscSystem);
