import React, { useEffect, useCallback } from 'react';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
  useRouteMatch,
} from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';

import { SystemJobTemplatesAPI } from '../../api';
import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
import NotificationList from '../../components/NotificationList';
import RoutedTabs from '../../components/RoutedTabs';
import { Schedules } from '../../components/Schedule';
import { useConfig } from '../../contexts/Config';
import useRequest from '../../util/useRequest';

import ManagementJobDetails from './ManagementJobDetails';
import ManagementJobEdit from './ManagementJobEdit';

function ManagementJob({ i18n, setBreadcrumb }) {
  const basePath = '/management_jobs';

  const match = useRouteMatch();
  const { id } = useParams();
  const { pathname } = useLocation();
  const { me, isNotificationAdmin } = useConfig();

  const canReadNotifications = isNotificationAdmin || me?.is_system_auditor;

  const { isLoading, error, request, result } = useRequest(
    useCallback(async () => SystemJobTemplatesAPI.readDetail(id), [id])
  );

  useEffect(() => {
    request();
  }, [request, pathname]);

  useEffect(() => {
    if (!result) return;

    setBreadcrumb(result);
  }, [result, setBreadcrumb]);

  const createSchedule = data =>
    SystemJobTemplatesAPI.createSchedule(result.id, data);
  const loadSchedules = params =>
    SystemJobTemplatesAPI.readSchedules(result.id, params);
  const loadScheduleOptions = () =>
    SystemJobTemplatesAPI.readScheduleOptions(result.id);

  const tabsArray = [
    {
      id: 99,
      link: basePath,
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to management jobs`)}
        </>
      ),
    },
    {
      id: 0,
      link: `${basePath}/${id}/details`,
      name: i18n._(t`Details`),
    },
    {
      id: 1,
      name: i18n._(t`Schedules`),
      link: `${match.url}/schedules`,
    },
  ];

  if (canReadNotifications) {
    tabsArray.push({
      id: 2,
      name: i18n._(t`Notifications`),
      link: `${match.url}/notifications`,
    });
  }

  let Tabs = <RoutedTabs tabsArray={tabsArray} />;
  if (pathname.includes('edit') || pathname.includes('schedules/')) {
    Tabs = null;
  }

  const LoadingScreen = (
    <PageSection>
      <Card>
        {Tabs}
        <ContentLoading />
      </Card>
    </PageSection>
  );

  const ErrorScreen = (
    <PageSection>
      <Card>
        <ContentError error={error}>
          {error?.response?.status === 404 && (
            <span>
              {i18n._(t`Management job not found.`)}
              {''}
              <Link to={basePath}>{i18n._(t`View all management jobs`)}</Link>
            </span>
          )}
        </ContentError>
      </Card>
    </PageSection>
  );

  if (error) {
    return ErrorScreen;
  }

  if (isLoading) {
    return LoadingScreen;
  }

  return (
    <PageSection>
      <Card>
        {Tabs}
        <Switch>
          <Redirect
            exact
            from={`${basePath}/:id`}
            to={`${basePath}/:id/details`}
          />
          <Route path={`${basePath}/:id/details`}>
            <ManagementJobDetails managementJob={result} />
          </Route>
          <Route path={`${basePath}/:id/edit`}>
            <ManagementJobEdit managementJob={result} />
          </Route>
          {canReadNotifications ? (
            <Route path={`${basePath}/:id/notifications`}>
              <NotificationList
                id={Number(result?.id)}
                canToggleNotifications={isNotificationAdmin}
                apiModel={SystemJobTemplatesAPI}
              />
            </Route>
          ) : null}
          <Route path={`${basePath}/:id/schedules`}>
            <Schedules
              unifiedJobTemplate={result}
              createSchedule={createSchedule}
              loadSchedules={loadSchedules}
              loadScheduleOptions={loadScheduleOptions}
              setBreadcrumb={setBreadcrumb}
            />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(ManagementJob);
