import React, { useState, useEffect, useCallback } from 'react';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
  useRouteMatch,
} from 'react-router-dom';

import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';

import { SystemJobTemplatesAPI, OrganizationsAPI } from 'api';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import NotificationList from 'components/NotificationList';
import RoutedTabs from 'components/RoutedTabs';
import { Schedules } from 'components/Schedule';
import { useConfig } from 'contexts/Config';
import useRequest from 'hooks/useRequest';

function ManagementJob({ setBreadcrumb }) {
  const basePath = '/management_jobs';

  const match = useRouteMatch();
  const { id } = useParams();
  const { pathname } = useLocation();
  const { me } = useConfig();

  const [isNotificationAdmin, setIsNotificationAdmin] = useState(false);

  const { isLoading, error, request, result } = useRequest(
    useCallback(
      () =>
        Promise.all([
          SystemJobTemplatesAPI.readDetail(id),
          OrganizationsAPI.read({
            page_size: 1,
            role_level: 'notification_admin_role',
          }),
        ]).then(([{ data: systemJobTemplate }, notificationRoles]) => ({
          systemJobTemplate,
          notificationRoles,
        })),
      [id]
    )
  );

  useEffect(() => {
    request();
  }, [request, pathname]);

  useEffect(() => {
    if (!result) return;
    setIsNotificationAdmin(
      Boolean(result?.notificationRoles?.data?.results?.length)
    );
    setBreadcrumb(result);
  }, [result, setBreadcrumb, setIsNotificationAdmin]);

  useEffect(() => {
    if (!result) return;

    setBreadcrumb(result);
  }, [result, setBreadcrumb]);

  const createSchedule = useCallback(
    (data) =>
      SystemJobTemplatesAPI.createSchedule(result?.systemJobTemplate.id, data),
    [result]
  );
  const loadSchedules = useCallback(
    (params) =>
      SystemJobTemplatesAPI.readSchedules(result?.systemJobTemplate.id, params),
    [result]
  );
  const loadScheduleOptions = useCallback(
    () =>
      SystemJobTemplatesAPI.readScheduleOptions(result?.systemJobTemplate.id),
    [result]
  );

  const shouldShowNotifications =
    result?.systemJobTemplate?.id &&
    (isNotificationAdmin || me?.is_system_auditor);
  const shouldShowSchedules = !!result?.systemJobTemplate?.id;

  const tabsArray = [
    {
      id: 99,
      link: basePath,
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to management jobs`}
        </>
      ),
      persistentFilterKey: 'managementJobs',
    },
  ];

  if (shouldShowSchedules) {
    tabsArray.push({
      id: 0,
      name: t`Schedules`,
      link: `${match.url}/schedules`,
    });
  }

  if (shouldShowNotifications) {
    tabsArray.push({
      id: 1,
      name: t`Notifications`,
      link: `${match.url}/notifications`,
    });
  }

  let Tabs = <RoutedTabs tabsArray={tabsArray} />;
  if (pathname.includes('edit') || pathname.includes('schedules/')) {
    Tabs = null;
  }

  if (error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error}>
            {error?.response?.status === 404 && (
              <span>
                {t`Management job not found.`}

                <Link to={basePath}>{t`View all management jobs`}</Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  if (isLoading) {
    return (
      <PageSection>
        <Card>
          {Tabs}
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }

  return (
    <PageSection>
      <Card>
        {Tabs}
        <Switch>
          <Redirect
            exact
            from={`${basePath}/:id`}
            to={`${basePath}/:id/schedules`}
          />
          {shouldShowNotifications ? (
            <Route path={`${basePath}/:id/notifications`}>
              <NotificationList
                id={Number(result?.systemJobTemplate?.id)}
                canToggleNotifications={isNotificationAdmin}
                apiModel={SystemJobTemplatesAPI}
              />
            </Route>
          ) : null}
          {shouldShowSchedules ? (
            <Route path={`${basePath}/:id/schedules`}>
              <Schedules
                apiModel={SystemJobTemplatesAPI}
                resource={result.systemJobTemplate}
                createSchedule={createSchedule}
                loadSchedules={loadSchedules}
                loadScheduleOptions={loadScheduleOptions}
                setBreadcrumb={setBreadcrumb}
              />
            </Route>
          ) : null}
        </Switch>
      </Card>
    </PageSection>
  );
}

export default ManagementJob;
