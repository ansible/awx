import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Card, PageSection } from '@patternfly/react-core';
import { Link, useParams } from 'react-router-dom';
import useRequest from '../../util/useRequest';
import ContentError from '../../components/ContentError';
import { NotificationTemplatesAPI } from '../../api';
import NotificationTemplateDetail from './NotificationTemplateDetail';

function NotificationTemplate({ i18n, setBreadcrumb }) {
  const { id: templateId } = useParams();
  const {
    result: template,
    isLoading,
    error,
    request: fetchTemplate,
  } = useRequest(
    useCallback(async () => {
      const { data } = await NotificationTemplatesAPI.readDetail(templateId);
      setBreadcrumb(data);
      return data;
    }, [templateId, setBreadcrumb]),
    null
  );

  useEffect(() => {
    fetchTemplate();
  }, [fetchTemplate]);

  if (error) {
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

  return (
    <PageSection>
      <Card>
        {template && (
          <NotificationTemplateDetail
            template={template}
            isLoading={isLoading}
          />
        )}
      </Card>
    </PageSection>
  );
}

export default withI18n()(NotificationTemplate);
