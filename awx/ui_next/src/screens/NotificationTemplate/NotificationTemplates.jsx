import React, { useState, useCallback } from 'react';
import { Route, Switch, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import NotificationTemplateList from './NotificationTemplateList';
import NotificationTemplateAdd from './NotificationTemplateAdd';
import NotificationTemplate from './NotificationTemplate';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

function NotificationTemplates({ i18n }) {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/notification_templates': i18n._(t`Notification Templates`),
    '/notification_templates/add': i18n._(t`Create New Notification Template`),
  });

  const updateBreadcrumbConfig = useCallback(
    notification => {
      const { id } = notification;
      setBreadcrumbConfig({
        '/notification_templates': i18n._(t`Notification Templates`),
        '/notification_templates/add': i18n._(
          t`Create New Notification Template`
        ),
        [`/notification_templates/${id}`]: notification.name,
        [`/notification_templates/${id}/edit`]: i18n._(t`Edit Details`),
        [`/notification_templates/${id}/details`]: i18n._(t`Details`),
      });
    },
    [i18n]
  );

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path={`${match.url}/add`}>
          <NotificationTemplateAdd />
        </Route>
        <Route path={`${match.url}/:id`}>
          <NotificationTemplate setBreadcrumb={updateBreadcrumbConfig} />
        </Route>
        <Route path={`${match.url}`}>
          <NotificationTemplateList />
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(NotificationTemplates);
