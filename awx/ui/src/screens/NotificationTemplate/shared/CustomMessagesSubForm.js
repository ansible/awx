import 'styled-components/macro';
import React, { useEffect, useRef } from 'react';

import { t } from '@lingui/macro';
import { useField, useFormikContext } from 'formik';
import { Switch, Text } from '@patternfly/react-core';
import { FormFullWidthLayout, SubFormLayout } from 'components/FormLayout';
import CodeEditorField from 'components/CodeEditor/CodeEditorField';
import { useConfig } from 'contexts/Config';
import getDocsBaseUrl from 'util/getDocsBaseUrl';

function CustomMessagesSubForm({ defaultMessages, type }) {
  const [useCustomField, , useCustomHelpers] = useField('useCustomMessages');
  const showMessages = type !== 'webhook';
  const showBodies = ['email', 'pagerduty', 'webhook'].includes(type);

  const { setFieldValue } = useFormikContext();
  const config = useConfig();
  const mountedRef = useRef(null);
  useEffect(
    () => {
      if (!mountedRef.current) {
        mountedRef.current = true;
        return;
      }
      const defs = defaultMessages[type];

      const resetFields = (name, defaults) => {
        setFieldValue(`${name}.message`, defaults.message || '');
        setFieldValue(`${name}.body`, defaults.body || '');
      };

      resetFields('messages.started', defs.started);
      resetFields('messages.success', defs.success);
      resetFields('messages.error', defs.error);
      resetFields(
        'messages.workflow_approval.approved',
        defs.workflow_approval.approved
      );
      resetFields(
        'messages.workflow_approval.denied',
        defs.workflow_approval.denied
      );
      resetFields(
        'messages.workflow_approval.running',
        defs.workflow_approval.running
      );
      resetFields(
        'messages.workflow_approval.timed_out',
        defs.workflow_approval.timed_out
      );
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [type, setFieldValue]
  );

  return (
    <>
      <Switch
        id="toggle-custom-messages"
        label={t`Customize messages…`}
        isChecked={!!useCustomField.value}
        onChange={() => useCustomHelpers.setValue(!useCustomField.value)}
      />
      {useCustomField.value && (
        <SubFormLayout>
          <Text
            className="pf-c-content"
            css="margin-bottom: var(--pf-c-content--MarginBottom)"
          >
            <small>
              {t`Use custom messages to change the content of
                notifications sent when a job starts, succeeds, or fails. Use
                curly braces to access information about the job:`}{' '}
              <code>
                {'{{'} job_friendly_name {'}}'}
              </code>
              ,{' '}
              <code>
                {'{{'} url {'}}'}
              </code>
              ,{' '}
              <code>
                {'{{'} job.status {'}}'}
              </code>
              .{' '}
              {t`You may apply a number of possible variables in the
                message. For more information, refer to the`}{' '}
              <a
                target="_blank"
                rel="noopener noreferrer"
                href={`${getDocsBaseUrl(
                  config
                )}/html/userguide/notifications.html#create-custom-notifications`}
              >
                {t`Ansible Controller Documentation.`}
              </a>
            </small>
          </Text>
          <FormFullWidthLayout>
            {showMessages && (
              <CodeEditorField
                id="start-message"
                name="messages.started.message"
                label={t`Start message`}
                mode="jinja2"
                rows={2}
              />
            )}
            {showBodies && (
              <CodeEditorField
                id="start-body"
                name="messages.started.body"
                label={t`Start message body`}
                mode="jinja2"
                rows={6}
              />
            )}
            {showMessages && (
              <CodeEditorField
                id="success-message"
                name="messages.success.message"
                label={t`Success message`}
                mode="jinja2"
                rows={2}
              />
            )}
            {showBodies && (
              <CodeEditorField
                id="success-body"
                name="messages.success.body"
                label={t`Success message body`}
                mode="jinja2"
                rows={6}
              />
            )}
            {showMessages && (
              <CodeEditorField
                id="error-message"
                name="messages.error.message"
                label={t`Error message`}
                mode="jinja2"
                rows={2}
              />
            )}
            {showBodies && (
              <CodeEditorField
                id="error-body"
                name="messages.error.body"
                label={t`Error message body`}
                mode="jinja2"
                rows={6}
              />
            )}
            {showMessages && (
              <CodeEditorField
                id="wf-approved-message"
                name="messages.workflow_approval.approved.message"
                label={t`Workflow approved message`}
                mode="jinja2"
                rows={2}
              />
            )}
            {showBodies && (
              <CodeEditorField
                id="wf-approved-body"
                name="messages.workflow_approval.approved.body"
                label={t`Workflow approved message body`}
                mode="jinja2"
                rows={6}
              />
            )}
            {showMessages && (
              <CodeEditorField
                id="wf-denied-message"
                name="messages.workflow_approval.denied.message"
                label={t`Workflow denied message`}
                mode="jinja2"
                rows={2}
              />
            )}
            {showBodies && (
              <CodeEditorField
                id="wf-denied-body"
                name="messages.workflow_approval.denied.body"
                label={t`Workflow denied message body`}
                mode="jinja2"
                rows={6}
              />
            )}
            {showMessages && (
              <CodeEditorField
                id="wf-running-message"
                name="messages.workflow_approval.running.message"
                label={t`Workflow pending message`}
                mode="jinja2"
                rows={2}
              />
            )}
            {showBodies && (
              <CodeEditorField
                id="wf-running-body"
                name="messages.workflow_approval.running.body"
                label={t`Workflow pending message body`}
                mode="jinja2"
                rows={6}
              />
            )}
            {showMessages && (
              <CodeEditorField
                id="wf-timed-out-message"
                name="messages.workflow_approval.timed_out.message"
                label={t`Workflow timed out message`}
                mode="jinja2"
                rows={2}
              />
            )}
            {showBodies && (
              <CodeEditorField
                id="wf-timed-out-body"
                name="messages.workflow_approval.timed_out.body"
                label={t`Workflow timed out message body`}
                mode="jinja2"
                rows={6}
              />
            )}
          </FormFullWidthLayout>
        </SubFormLayout>
      )}
    </>
  );
}

export default CustomMessagesSubForm;
