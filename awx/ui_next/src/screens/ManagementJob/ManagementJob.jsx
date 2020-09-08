import React, { useEffect, useCallback } from 'react';
import {
  Link,
  Redirect,
  Route,
  Switch,
  useLocation,
  useParams,
} from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CaretLeftIcon } from '@patternfly/react-icons';
import { Card, PageSection } from '@patternfly/react-core';
import { useRouteMatch } from 'react-router-dom';

import { SystemJobTemplatesAPI } from '../../api';

import ContentError from '../../components/ContentError';
import ContentLoading from '../../components/ContentLoading';
import RoutedTabs from '../../components/RoutedTabs';
import { useConfig } from '../../contexts/Config';
import useRequest from '../../util/useRequest';

import ManagementJobDetails from './ManagementJobDetails';
import ManagementJobEdit from './ManagementJobEdit';
import ManagementJobNotifications from './ManagementJobNotifications';
import ManagementJobSchedules from './ManagementJobSchedules';

function ManagementJob({ i18n, setBreadcrumb }) {
  const segment = '/management_jobs';

  const match = useRouteMatch();
  const { id } = useParams();
  const { pathname } = useLocation();
  const { me, isNotificationAdmin } = useConfig();

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

  const tabsArray = [
    {
      id: 99,
      link: segment,
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to management jobs`)}
        </>
      ),
    },
    {
      id: 0,
      link: `${segment}/${id}/details`,
      name: i18n._(t`Details`),
    },
    {
      id: 1,
      name: i18n._(t`Schedules`),
      link: `${match.url}/schedules`,
    },
  ];

  if (me?.is_system_auditor || isNotificationAdmin) {
    tabsArray.push({
      id: 2,
      name: i18n._(t`Notifications`),
      link: `${match.url}/notifications`,
    });
  }

  const LoadingScreen = (
    <PageSection>
      <Card>
        {pathname.endsWith('edit') ? null : (
          <RoutedTabs tabsArray={tabsArray} />
        )}
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
              <Link to={segment}>{i18n._(t`View all management jobs`)}</Link>
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
        {pathname.endsWith('edit') ? null : (
          <RoutedTabs tabsArray={tabsArray} />
        )}
        <Switch>
          <Redirect
            exact
            from={`${segment}/:id`}
            to={`${segment}/:id/details`}
          />
          <Route path={`${segment}/:id/details`}>
            <ManagementJobDetails managementJob={result} />
          </Route>
          <Route path={`${segment}/:id/edit`}>
            <ManagementJobEdit managementJob={result} />
          </Route>
          <Route path={`${segment}/:id/notifications`}>
            <ManagementJobNotifications managementJob={result} />
          </Route>
          <Route path={`${segment}/:id/schedules`}>
            <ManagementJobSchedules managementJob={result} />
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(ManagementJob);
