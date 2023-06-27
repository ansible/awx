import React, { useCallback, useEffect } from 'react';
import { Link, Route, Switch, Redirect } from 'react-router-dom';
import { t } from '@lingui/macro';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import ScreenHeader from 'components/ScreenHeader';
import { SettingsProvider } from 'contexts/Settings';
import { useConfig } from 'contexts/Config';
import { SettingsAPI } from 'api';
import useRequest from 'hooks/useRequest';
import AzureAD from './AzureAD';
import GitHub from './GitHub';
import GoogleOAuth2 from './GoogleOAuth2';
import OIDC from './OIDC';
import Jobs from './Jobs';
import LDAP from './LDAP';
import Subscription from './Subscription';
import Logging from './Logging';
import MiscAuthentication from './MiscAuthentication';
import MiscSystem from './MiscSystem';
import RADIUS from './RADIUS';
import SAML from './SAML';
import SettingList from './SettingList';
import TACACS from './TACACS';
import UI from './UI';
import Troubleshooting from './Troubleshooting';

function Settings() {
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
    '/settings': t`Settings`,
    '/settings/activity_stream': t`Activity Stream`,
    '/settings/activity_stream/details': t`Details`,
    '/settings/activity_stream/edit': t`Edit Details`,
    '/settings/azure': t`Azure AD`,
    '/settings/azure/details': t`Details`,
    '/settings/azure/edit': t`Edit Details`,
    '/settings/github': null,
    '/settings/github/default': t`GitHub Default`,
    '/settings/github/default/details': t`Details`,
    '/settings/github/default/edit': t`Edit Details`,
    '/settings/github/organization': t`GitHub Organization`,
    '/settings/github/organization/details': t`Details`,
    '/settings/github/organization/edit': t`Edit Details`,
    '/settings/github/team': t`GitHub Team`,
    '/settings/github/team/details': t`Details`,
    '/settings/github/team/edit': t`Edit Details`,
    '/settings/github/enterprise': t`GitHub Enterprise`,
    '/settings/github/enterprise/details': t`Details`,
    '/settings/github/enterprise/edit': t`Edit Details`,
    '/settings/github/enterprise_organization': t`GitHub Enterprise Organization`,
    '/settings/github/enterprise_organization/details': t`Details`,
    '/settings/github/enterprise_organization/edit': t`Edit Details`,
    '/settings/github/enterprise_team': t`GitHub Enterprise Team`,
    '/settings/github/enterprise_team/details': t`Details`,
    '/settings/github/enterprise_team/edit': t`Edit Details`,
    '/settings/google_oauth2': t`Google OAuth2`,
    '/settings/google_oauth2/details': t`Details`,
    '/settings/google_oauth2/edit': t`Edit Details`,
    '/settings/oidc': t`Generic OIDC`,
    '/settings/oidc/details': t`Details`,
    '/settings/oidc/edit': t`Edit Details`,
    '/settings/jobs': t`Jobs`,
    '/settings/jobs/details': t`Details`,
    '/settings/jobs/edit': t`Edit Details`,
    '/settings/ldap': null,
    '/settings/ldap/default': t`LDAP Default`,
    '/settings/ldap/1': t`LDAP 1`,
    '/settings/ldap/2': t`LDAP 2`,
    '/settings/ldap/3': t`LDAP 3`,
    '/settings/ldap/4': t`LDAP 4`,
    '/settings/ldap/5': t`LDAP 5`,
    '/settings/ldap/default/details': t`Details`,
    '/settings/ldap/1/details': t`Details`,
    '/settings/ldap/2/details': t`Details`,
    '/settings/ldap/3/details': t`Details`,
    '/settings/ldap/4/details': t`Details`,
    '/settings/ldap/5/details': t`Details`,
    '/settings/ldap/default/edit': t`Edit Details`,
    '/settings/ldap/1/edit': t`Edit Details`,
    '/settings/ldap/2/edit': t`Edit Details`,
    '/settings/ldap/3/edit': t`Edit Details`,
    '/settings/ldap/4/edit': t`Edit Details`,
    '/settings/ldap/5/edit': t`Edit Details`,
    '/settings/logging': t`Logging`,
    '/settings/logging/details': t`Details`,
    '/settings/logging/edit': t`Edit Details`,
    '/settings/miscellaneous_authentication': t`Miscellaneous Authentication`,
    '/settings/miscellaneous_authentication/details': t`Details`,
    '/settings/miscellaneous_authentication/edit': t`Edit Details`,
    '/settings/miscellaneous_system': t`Miscellaneous System`,
    '/settings/miscellaneous_system/details': t`Details`,
    '/settings/miscellaneous_system/edit': t`Edit Details`,
    '/settings/radius': t`RADIUS`,
    '/settings/radius/details': t`Details`,
    '/settings/radius/edit': t`Edit Details`,
    '/settings/saml': t`SAML`,
    '/settings/saml/details': t`Details`,
    '/settings/saml/edit': t`Edit Details`,
    '/settings/subscription': t`Subscription`,
    '/settings/subscription/details': t`Details`,
    '/settings/subscription/edit': t`Edit Details`,
    '/settings/tacacs': t`TACACS+`,
    '/settings/tacacs/details': t`Details`,
    '/settings/tacacs/edit': t`Edit Details`,
    '/settings/ui': t`User Interface`,
    '/settings/ui/details': t`Details`,
    '/settings/ui/edit': t`Edit Details`,
    '/settings/troubleshooting': t`Troubleshooting`,
    '/settings/troubleshooting/details': t`Details`,
    '/settings/troubleshooting/edit': t`Edit Details`,
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
      <ScreenHeader streamType="setting" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/settings/azure">
          <AzureAD />
        </Route>
        <Route path="/settings/github">
          <GitHub />
        </Route>
        <Route path="/settings/google_oauth2">
          <GoogleOAuth2 />
        </Route>
        <Route path="/settings/oidc">
          <OIDC />
        </Route>
        <Route path="/settings/jobs">
          <Jobs />
        </Route>
        <Route path="/settings/ldap">
          <LDAP />
        </Route>
        <Route path="/settings/subscription">
          {license_info?.license_type === 'open' ? (
            <Redirect to="/settings" />
          ) : (
            <Subscription />
          )}
        </Route>
        <Route path="/settings/logging">
          <Logging />
        </Route>
        <Route path="/settings/miscellaneous_authentication">
          <MiscAuthentication />
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
        <Route path="/settings/troubleshooting">
          <Troubleshooting />
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
                <Link to="/settings">{t`View all settings`}</Link>
              </ContentError>
            </Card>
          </PageSection>
        </Route>
      </Switch>
    </SettingsProvider>
  );
}

export default Settings;
