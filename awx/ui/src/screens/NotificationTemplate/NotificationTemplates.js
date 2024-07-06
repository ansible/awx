import React, { useState, useCallback } from 'react';
import { Route, Switch, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import NotificationTemplateList from './NotificationTemplateList';
import NotificationTemplateAdd from './NotificationTemplateAdd';
import NotificationTemplate from './NotificationTemplate';

function NotificationTemplates() {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/notification_templates': t`Notification Templates`,
    '/notification_templates/add': t`Create New Notification Template`,
  });

  const updateBreadcrumbConfig = useCallback((notification) => {
    const { id } = notification;
    setBreadcrumbConfig({
      '/notification_templates': t`Notification Templates`,
      '/notification_templates/add': t`Create New Notification Template`,
      [`/notification_templates/${id}`]: notification.name,
      [`/notification_templates/${id}/edit`]: t`Edit Details`,
      [`/notification_templates/${id}/details`]: t`Details`,
    });
  }, []);

  const [activityStream, setActivityStream] = useState({
    streamType: 'notification_template',
  });
  const buildActivityStream = useCallback(
    (item) => {
      item && setActivityStream({ ...activityStream, streamId: item.id });
    },
    [activityStream]
  );

  return (
    <>
      <ScreenHeader
        activityStream={activityStream}
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path={`${match.url}/add`}>
          <NotificationTemplateAdd />
        </Route>
        <Route path={`${match.url}/:id`}>
          <NotificationTemplate
            setBreadcrumb={updateBreadcrumbConfig}
            buildActivityStream={buildActivityStream}
          />
        </Route>
        <Route path={`${match.url}`}>
          <PersistentFilters pageKey="notificationTemplates">
            <NotificationTemplateList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export default NotificationTemplates;
