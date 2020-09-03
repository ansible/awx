import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import GoogleOAuth2Detail from './GoogleOAuth2Detail';
import GoogleOAuth2Edit from './GoogleOAuth2Edit';

function GoogleOAuth2({ i18n }) {
  const baseUrl = '/settings/google_oauth2';

  return (
    <PageSection>
      <Card>
        {i18n._(t`Google OAuth 2.0 settings`)}
        <Switch>
          <Redirect from={baseUrl} to={`${baseUrl}/details`} exact />
          <Route path={`${baseUrl}/details`}>
            <GoogleOAuth2Detail />
          </Route>
          <Route path={`${baseUrl}/edit`}>
            <GoogleOAuth2Edit />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(GoogleOAuth2);
