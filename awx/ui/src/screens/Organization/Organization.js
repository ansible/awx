import React, { useCallback, useEffect, useRef } from 'react';

import { t } from '@lingui/macro';
import {
  Switch,
  Route,
  Redirect,
  Link,
  useLocation,
  useParams,
  useRouteMatch,
} from 'react-router-dom';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import useRequest from 'hooks/useRequest';
import RoutedTabs from 'components/RoutedTabs';
import ContentError from 'components/ContentError';
import NotificationList from 'components/NotificationList/NotificationList';
import { ResourceAccessList } from 'components/ResourceAccessList';
import { OrganizationsAPI } from 'api';
import OrganizationDetail from './OrganizationDetail';
import OrganizationEdit from './OrganizationEdit';
import OrganizationTeams from './OrganizationTeams';
import OrganizationExecEnvList from './OrganizationExecEnvList';

function Organization({ setBreadcrumb, me }) {
  const location = useLocation();
  const { id: organizationId } = useParams();
  const match = useRouteMatch();
  const initialUpdate = useRef(true);

  const {
    result: { organization },
    isLoading: organizationLoading,
    error: organizationError,
    request: loadOrganization,
  } = useRequest(
    useCallback(async () => {
      const [{ data }, credentialsRes] = await Promise.all([
        OrganizationsAPI.readDetail(organizationId),
        OrganizationsAPI.readGalaxyCredentials(organizationId),
      ]);
      data.galaxy_credentials = credentialsRes.data.results;
      setBreadcrumb(data);

      return {
        organization: data,
      };
    }, [setBreadcrumb, organizationId]),
    {
      organization: null,
    }
  );

  const {
    result: { isNotifAdmin, isAuditorOfThisOrg, isAdminOfThisOrg },
    isLoading: rolesLoading,
    error: rolesError,
    request: loadRoles,
  } = useRequest(
    useCallback(async () => {
      const [notifAdminRes, auditorRes, adminRes] = await Promise.all([
        OrganizationsAPI.read({
          page_size: 1,
          role_level: 'notification_admin_role',
        }),
        OrganizationsAPI.read({
          id: organizationId,
          role_level: 'auditor_role',
        }),
        OrganizationsAPI.read({
          id: organizationId,
          role_level: 'admin_role',
        }),
      ]);

      return {
        isNotifAdmin: notifAdminRes.data.results.length > 0,
        isAuditorOfThisOrg: auditorRes.data.results.length > 0,
        isAdminOfThisOrg: adminRes.data.results.length > 0,
      };
    }, [organizationId]),
    {
      isNotifAdmin: false,
      isAuditorOfThisOrg: false,
      isAdminOfThisOrg: false,
    }
  );
  useEffect(() => {
    loadOrganization();
    loadRoles();
  }, [loadOrganization, loadRoles]);

  useEffect(() => {
    if (initialUpdate.current) {
      initialUpdate.current = false;
      return;
    }

    if (location.pathname === `/organizations/${organizationId}/details`) {
      loadOrganization();
    }
  }, [loadOrganization, organizationId, location.pathname]);

  const canSeeNotificationsTab =
    me.is_system_auditor || isNotifAdmin || isAuditorOfThisOrg;
  const canToggleNotifications =
    isNotifAdmin &&
    (me.is_system_auditor || isAuditorOfThisOrg || isAdminOfThisOrg);

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Organizations`}
        </>
      ),
      link: `/organizations`,
      id: 99,
      persistentFilterKey: 'organizations',
    },
    { name: t`Details`, link: `${match.url}/details`, id: 0 },
    { name: t`Access`, link: `${match.url}/access`, id: 1 },
    { name: t`Teams`, link: `${match.url}/teams`, id: 2 },
    {
      name: t`Execution Environments`,
      link: `${match.url}/execution_environments`,
      id: 4,
    },
  ];

  if (canSeeNotificationsTab) {
    tabsArray.push({
      name: t`Notifications`,
      link: `${match.url}/notifications`,
      id: 3,
    });
  }

  let showCardHeader = true;

  if (location.pathname.endsWith('edit')) {
    showCardHeader = false;
  }

  if (!organizationLoading && organizationError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={organizationError}>
            {organizationError.response.status === 404 && (
              <span>
                {t`Organization not found.`}{' '}
                <Link to="/organizations">{t`View all Organizations.`}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  if (!rolesLoading && rolesError) {
    return (
      <PageSection>
        <Card>
          <ContentError error={rolesError} />
        </Card>
      </PageSection>
    );
  }

  return (
    <PageSection>
      <Card>
        {showCardHeader && <RoutedTabs tabsArray={tabsArray} />}
        <Switch>
          <Redirect
            from="/organizations/:id"
            to="/organizations/:id/details"
            exact
          />
          {organization && (
            <Route path="/organizations/:id/edit">
              <OrganizationEdit organization={organization} />
            </Route>
          )}
          {organization && (
            <Route path="/organizations/:id/details">
              <OrganizationDetail organization={organization} />
            </Route>
          )}
          {organization && (
            <Route path="/organizations/:id/access">
              <ResourceAccessList
                resource={organization}
                apiModel={OrganizationsAPI}
              />
            </Route>
          )}
          <Route path="/organizations/:id/teams">
            <OrganizationTeams id={Number(match.params.id)} />
          </Route>
          {canSeeNotificationsTab && (
            <Route path="/organizations/:id/notifications">
              <NotificationList
                id={Number(match.params.id)}
                canToggleNotifications={canToggleNotifications}
                apiModel={OrganizationsAPI}
                showApprovalsToggle
              />
            </Route>
          )}
          {organization && (
            <Route path="/organizations/:id/execution_environments">
              <OrganizationExecEnvList organization={organization} />
            </Route>
          )}
          <Route key="not-found" path="*">
            {!organizationLoading && !rolesLoading && (
              <ContentError isNotFound>
                {match.params.id && (
                  <Link to={`/organizations/${match.params.id}/details`}>
                    {t`View Organization Details`}
                  </Link>
                )}
              </ContentError>
            )}
          </Route>
          ,
        </Switch>
      </Card>
    </PageSection>
  );
}

export default Organization;
export { Organization as _Organization };
