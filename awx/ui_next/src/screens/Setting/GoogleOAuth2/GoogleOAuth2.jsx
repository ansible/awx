import React from 'react';
import { Link, Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../../components/ContentError';
import GoogleOAuth2Detail from './GoogleOAuth2Detail';
import GoogleOAuth2Edit from './GoogleOAuth2Edit';

function GoogleOAuth2({ i18n }) {
  const baseURL = '/settings/google_oauth2';
  return (
    <PageSection>
      <Card>
        <Switch>
          <Redirect from={baseURL} to={`${baseURL}/details`} exact />
          <Route path={`${baseURL}/details`}>
            <GoogleOAuth2Detail />
          </Route>
          <Route path={`${baseURL}/edit`}>
            <GoogleOAuth2Edit />
          </Route>
          <Route key="not-found" path={`${baseURL}/*`}>
            <ContentError isNotFound>
              <Link to={`${baseURL}/details`}>
                {i18n._(t`View Google OAuth 2.0 settings`)}
              </Link>
            </ContentError>
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(GoogleOAuth2);
