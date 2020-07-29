import React from 'react';
import { Link, Route, Switch, Redirect } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../components/ContentError';
import Breadcrumbs from '../../components/Breadcrumbs';
import ActivityStream from './ActivityStream';
import AzureAD from './AzureAD';
import GitHub from './GitHub';
import GoogleOAuth2 from './GoogleOAuth2';
import Jobs from './Jobs';
import LDAP from './LDAP';
import License from './License';
import Logging from './Logging';
import MiscSystem from './MiscSystem';
import Radius from './Radius';
import SAML from './SAML';
import SettingList from './SettingList';
import TACACS from './TACACS';
import UI from './UI';
import { useConfig } from '../../contexts/Config';

function Settings({ i18n }) {
  const { license_info = {} } = useConfig();
  const breadcrumbConfig = {
    '/settings': i18n._(t`Settings`),
    '/settings/activity_stream': i18n._(t`Activity stream`),
    '/settings/azure': i18n._(t`Azure AD`),
    '/settings/github': i18n._(t`GitHub`),
    '/settings/google_oauth2': i18n._(t`Google OAuth2`),
    '/settings/jobs': i18n._(t`Jobs`),
    '/settings/ldap': i18n._(t`LDAP`),
    '/settings/license': i18n._(t`License`),
    '/settings/logging': i18n._(t`Logging`),
    '/settings/miscellaneous_system': i18n._(t`Miscellaneous system`),
    '/settings/radius': i18n._(t`Radius`),
    '/settings/saml': i18n._(t`SAML`),
    '/settings/tacacs': i18n._(t`TACACS+`),
    '/settings/user_interface': i18n._(t`User interface`),
  };

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/settings/activity_stream">
          <ActivityStream />
        </Route>
        <Route path="/settings/azure">
          <AzureAD />
        </Route>
        <Route path="/settings/github">
          <GitHub />
        </Route>
        <Route path="/settings/google_oauth2">
          <GoogleOAuth2 />
        </Route>
        <Route path="/settings/jobs">
          <Jobs />
        </Route>
        <Route path="/settings/ldap">
          <LDAP />
        </Route>
        <Route path="/settings/license">
          {license_info?.license_type === 'open' ? (
            <License />
          ) : (
            <Redirect to="/settings" />
          )}
        </Route>
        <Route path="/settings/logging">
          <Logging />
        </Route>
        <Route path="/settings/miscellaneous_system">
          <MiscSystem />
        </Route>
        <Route path="/settings/radius">
          <Radius />
        </Route>
        <Route path="/settings/saml">
          <SAML />
        </Route>
        <Route path="/settings/tacacs">
          <TACACS />
        </Route>
        <Route path="/settings/user_interface">
          <UI />
        </Route>
        <Route path="/settings" exact>
          <SettingList />
        </Route>
        <Route key="not-found" path="*">
          <PageSection>
            <Card>
              <ContentError isNotFound>
                <Link to="/settings">{i18n._(t`View all settings`)}</Link>
              </ContentError>
            </Card>
          </PageSection>
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(Settings);
