import React, { useCallback, useEffect } from 'react';
import { Link, Route, Switch, Redirect } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
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
import RADIUS from './RADIUS';
import SAML from './SAML';
import SettingList from './SettingList';
import TACACS from './TACACS';
import UI from './UI';
import { SettingsProvider } from '../../contexts/Settings';
import { useConfig } from '../../contexts/Config';
import { SettingsAPI } from '../../api';
import useRequest from '../../util/useRequest';

function Settings({ i18n }) {
  const { license_info = {}, me } = useConfig();

  const { request, result, isLoading, error } = useRequest(
    useCallback(async () => {
      const response = await SettingsAPI.readAllOptions();
      return response.data.actions;
    }, [])
  );

  useEffect(() => {
    request();
  }, [request]);

  const breadcrumbConfig = {
    '/settings': i18n._(t`Settings`),
    '/settings/activity_stream': i18n._(t`Activity Stream`),
    '/settings/activity_stream/details': i18n._(t`Details`),
    '/settings/activity_stream/edit': i18n._(t`Edit Details`),
    '/settings/azure': i18n._(t`Azure AD`),
    '/settings/azure/details': i18n._(t`Details`),
    '/settings/azure/edit': i18n._(t`Edit Details`),
    '/settings/github': null,
    '/settings/github/default': i18n._(t`GitHub Default`),
    '/settings/github/default/details': i18n._(t`Details`),
    '/settings/github/default/edit': i18n._(t`Edit Details`),
    '/settings/github/organization': i18n._(t`GitHub Organization`),
    '/settings/github/organization/details': i18n._(t`Details`),
    '/settings/github/organization/edit': i18n._(t`Edit Details`),
    '/settings/github/team': i18n._(t`GitHub Team`),
    '/settings/github/team/details': i18n._(t`Details`),
    '/settings/github/team/edit': i18n._(t`Edit Details`),
    '/settings/google_oauth2': i18n._(t`Google OAuth2`),
    '/settings/google_oauth2/details': i18n._(t`Details`),
    '/settings/google_oauth2/edit': i18n._(t`Edit Details`),
    '/settings/jobs': i18n._(t`Jobs`),
    '/settings/jobs/details': i18n._(t`Details`),
    '/settings/jobs/edit': i18n._(t`Edit Details`),
    '/settings/ldap': null,
    '/settings/ldap/default': i18n._(t`LDAP Default`),
    '/settings/ldap/1': i18n._(t`LDAP 1`),
    '/settings/ldap/2': i18n._(t`LDAP 2`),
    '/settings/ldap/3': i18n._(t`LDAP 3`),
    '/settings/ldap/4': i18n._(t`LDAP 4`),
    '/settings/ldap/5': i18n._(t`LDAP 5`),
    '/settings/ldap/default/details': i18n._(t`Details`),
    '/settings/ldap/1/details': i18n._(t`Details`),
    '/settings/ldap/2/details': i18n._(t`Details`),
    '/settings/ldap/3/details': i18n._(t`Details`),
    '/settings/ldap/4/details': i18n._(t`Details`),
    '/settings/ldap/5/details': i18n._(t`Details`),
    '/settings/ldap/default/edit': i18n._(t`Edit Details`),
    '/settings/ldap/1/edit': i18n._(t`Edit Details`),
    '/settings/ldap/2/edit': i18n._(t`Edit Details`),
    '/settings/ldap/3/edit': i18n._(t`Edit Details`),
    '/settings/ldap/4/edit': i18n._(t`Edit Details`),
    '/settings/ldap/5/edit': i18n._(t`Edit Details`),
    '/settings/license': i18n._(t`License`),
    '/settings/logging': i18n._(t`Logging`),
    '/settings/logging/details': i18n._(t`Details`),
    '/settings/logging/edit': i18n._(t`Edit Details`),
    '/settings/miscellaneous_system': i18n._(t`Miscellaneous System`),
    '/settings/miscellaneous_system/details': i18n._(t`Details`),
    '/settings/miscellaneous_system/edit': i18n._(t`Edit Details`),
    '/settings/radius': i18n._(t`RADIUS`),
    '/settings/radius/details': i18n._(t`Details`),
    '/settings/radius/edit': i18n._(t`Edit Details`),
    '/settings/saml': i18n._(t`SAML`),
    '/settings/saml/details': i18n._(t`Details`),
    '/settings/saml/edit': i18n._(t`Edit Details`),
    '/settings/tacacs': i18n._(t`TACACS+`),
    '/settings/tacacs/details': i18n._(t`Details`),
    '/settings/tacacs/edit': i18n._(t`Edit Details`),
    '/settings/ui': i18n._(t`User Interface`),
    '/settings/ui/details': i18n._(t`Details`),
    '/settings/ui/edit': i18n._(t`Edit Details`),
  };

  if (error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error} />
        </Card>
      </PageSection>
    );
  }

  if (isLoading || !result || !me) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }

  if (!me?.is_superuser && !me?.is_system_auditor) {
    return <Redirect to="/" />;
  }

  return (
    <SettingsProvider value={result}>
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
          <RADIUS />
        </Route>
        <Route path="/settings/saml">
          <SAML />
        </Route>
        <Route path="/settings/tacacs">
          <TACACS />
        </Route>
        <Route path="/settings/ui">
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
    </SettingsProvider>
  );
}

export default withI18n()(Settings);
