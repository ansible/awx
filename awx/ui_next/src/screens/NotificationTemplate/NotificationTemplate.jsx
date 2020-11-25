import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, PageSection } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import {
  Link,
  Switch,
  Route,
  Redirect,
  useParams,
  useRouteMatch,
  useLocation,
} from 'react-router-dom';
import useRequest from '../../util/useRequest';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import { NotificationTemplatesAPI } from '../../api';
import NotificationTemplateDetail from './NotificationTemplateDetail';
import NotificationTemplateEdit from './NotificationTemplateEdit';
import ContentLoading from '../../components/ContentLoading';

function NotificationTemplate({ setBreadcrumb, i18n }) {
  const { id: templateId } = useParams();
  const match = useRouteMatch();
  const location = useLocation();
  const {
    result: { template, defaultMessages },
    isLoading,
    error,
    request: fetchTemplate,
  } = useRequest(
    useCallback(async () => {
      const [detail, options] = await Promise.all([
        NotificationTemplatesAPI.readDetail(templateId),
        NotificationTemplatesAPI.readOptions(),
      ]);
      setBreadcrumb(detail.data);
      return {
        template: detail.data,
        defaultMessages: options.data.actions.POST.messages,
      };
    }, [templateId, setBreadcrumb]),
    { template: null, defaultMessages: null }
  );

  useEffect(() => {
    fetchTemplate();
  }, [fetchTemplate, location.pathname]);

  if (!isLoading && error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error}>
            {error.response.status === 404 && (
              <span>
                {i18n._(t`Notification Template not found.`)}{' '}
                <Link to="/notification_templates">
                  {i18n._(t`View all Notification Templates.`)}
                </Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  const showCardHeader = !location.pathname.endsWith('edit');
  const tabs = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {i18n._(t`Back to Notifications`)}
        </>
      ),
      link: `/notification_templates`,
      id: 99,
    },
    {
      name: i18n._(t`Details`),
      link: `${match.url}/details`,
      id: 0,
    },
  ];
  return (
    <PageSection>
      <Card>
        {showCardHeader && <RoutedTabs tabsArray={tabs} />}
        <Switch>
          <Redirect
            from="/notification_templates/:id"
            to="/notification_templates/:id/details"
            exact
          />
          {isLoading && <ContentLoading />}
          {template && (
            <>
              <Route path="/notification_templates/:id/edit">
                <NotificationTemplateEdit
                  template={template}
                  defaultMessages={defaultMessages}
                />
              </Route>
              <Route path="/notification_templates/:id/details">
                <NotificationTemplateDetail
                  template={template}
                  defaultMessages={defaultMessages}
                />
              </Route>
            </>
          )}
        </Switch>
      </Card>
    </PageSection>
  );
}

export default withI18n()(NotificationTemplate);
