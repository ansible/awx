import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import NotificationTemplateForm from './NotificationTemplateForm';

jest.mock('../../../api/models/NotificationTemplates');

const template = {
  id: 3,
  notification_type: 'slack',
  name: 'Test Notification',
  description: 'a sample notification',
  url: '/notification_templates/3',
  organization: 1,
  summary_fields: {
    user_capabilities: {
      edit: true,
    },
    recent_notifications: [
      {
        status: 'success',
      },
    ],
    organization: {
      id: 1,
      name: 'The Organization',
    },
  },
};

const messageDef = {
  message: 'default message',
  body: 'default body',
};
const defaults = {
  started: messageDef,
  success: messageDef,
  error: messageDef,
  workflow_approval: {
    approved: messageDef,
    denied: messageDef,
    running: messageDef,
    timed_out: messageDef,
  },
};
const defaultMessages = {
  email: defaults,
  slack: defaults,
  twilio: defaults,
};

describe('<NotificationTemplateForm />', () => {
  test('should render form fields', () => {
    const wrapper = mountWithContexts(
      <NotificationTemplateForm
        template={template}
        defaultMessages={defaultMessages}
        detailUrl="/notification_templates/3/detail"
        onSubmit={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    expect(wrapper.find('input#notification-name').prop('value')).toEqual(
      'Test Notification'
    );
    expect(
      wrapper.find('input#notification-description').prop('value')
    ).toEqual('a sample notification');
    expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
      id: 1,
      name: 'The Organization',
    });
    expect(wrapper.find('AnsibleSelect').prop('value')).toEqual('slack');
    expect(wrapper.find('TypeInputsSubForm').prop('type')).toEqual('slack');
    expect(wrapper.find('CustomMessagesSubForm').prop('type')).toEqual('slack');
    expect(
      wrapper.find('CustomMessagesSubForm').prop('defaultMessages')
    ).toEqual(defaultMessages);
  });

  test('should submit', async () => {
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <NotificationTemplateForm
        template={{
          ...template,
          notification_configuration: {
            channels: ['#foo'],
            token: 'abc123',
          },
        }}
        defaultMessages={defaultMessages}
        detailUrl="/notification_templates/3/detail"
        onSubmit={handleSubmit}
        onCancel={jest.fn()}
      />
    );

    await act(async () => {
      wrapper.find('FormActionGroup').invoke('onSubmit')();
    });
    wrapper.update();

    expect(handleSubmit).toHaveBeenCalledWith({
      name: 'Test Notification',
      description: 'a sample notification',
      organization: 1,
      notification_type: 'slack',
      notification_configuration: {
        channels: ['#foo'],
        hex_color: '',
        token: 'abc123',
      },
      messages: null,
    });
  });
});
