import React, { useState, useEffect, useCallback } from 'react';
import { useHistory, Link } from 'react-router-dom';
import { t } from '@lingui/macro';

import { Card, PageSection } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import { NotificationTemplatesAPI } from 'api';
import useRequest from 'hooks/useRequest';
import ContentError from 'components/ContentError';
import NotificationTemplateForm from './shared/NotificationTemplateForm';

function NotificationTemplateAdd() {
  const history = useHistory();
  const [formError, setFormError] = useState(null);
  const {
    result: defaultMessages,
    error,
    request: fetchDefaultMessages,
  } = useRequest(
    useCallback(async () => {
      const { data } = await NotificationTemplatesAPI.readOptions();
      return data.actions.POST.messages;
    }, [])
  );

  useEffect(() => {
    fetchDefaultMessages();
  }, [fetchDefaultMessages]);

  const handleSubmit = async (values) => {
    try {
      const { data } = await NotificationTemplatesAPI.create(values);
      history.push(`/notification_templates/${data.id}`);
    } catch (err) {
      setFormError(err);
    }
  };

  const handleCancel = () => {
    history.push('/notification_templates');
  };

  if (error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error}>
            {error.response.status === 404 && (
              <span>
                {t`Notification Template not found.`}{' '}
                <Link to="/notification_templates">
                  {t`View all Notification Templates.`}
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
        <CardBody>
          {defaultMessages && (
            <NotificationTemplateForm
              defaultMessages={defaultMessages}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              submitError={formError}
            />
          )}
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { NotificationTemplateAdd as _NotificationTemplateAdd };
export default NotificationTemplateAdd;
