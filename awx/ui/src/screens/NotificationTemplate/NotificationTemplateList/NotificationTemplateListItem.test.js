import React from 'react';
import { act } from 'react-dom/test-utils';
import { NotificationTemplatesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import NotificationTemplateListItem from './NotificationTemplateListItem';

jest.mock('../../../api/models/NotificationTemplates');
jest.mock('../../../api/models/Notifications');

const template = {
  id: 3,
  notification_type: 'slack',
  name: 'Test Notification',
  summary_fields: {
    organization: {
      id: 1,
      name: 'Foo',
    },
    user_capabilities: {
      edit: true,
      copy: true,
    },
    recent_notifications: [
      {
        status: 'success',
      },
    ],
  },
};

describe('<NotificationTemplateListItem />', () => {
  test('should render template row', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationTemplateListItem
            template={template}
            onAddToast={jest.fn()}
            detailUrl="/notification_templates/3/detail"
          />
        </tbody>
      </table>
    );

    const cells = wrapper.find('Td');
    expect(cells).toHaveLength(6);
    expect(cells.at(1).text()).toEqual('Test Notification');
    expect(cells.at(2).text()).toEqual('Success');
    expect(cells.at(3).text()).toEqual('Slack');
  });

  test('should send test notification', async () => {
    NotificationTemplatesAPI.test.mockResolvedValue({
      data: { notification: 1 },
    });

    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationTemplateListItem
            template={template}
            onAddToast={jest.fn()}
            detailUrl="/notification_templates/3/detail"
          />
        </tbody>
      </table>
    );
    await act(async () => {
      wrapper.find('Button').at(0).invoke('onClick')();
    });
    expect(NotificationTemplatesAPI.test).toHaveBeenCalledTimes(1);
    expect(wrapper.find('Td').at(2).text()).toEqual('Running');
  });

  test('should call api to copy inventory', async () => {
    NotificationTemplatesAPI.copy.mockResolvedValue({ name: 'Foo' });

    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationTemplateListItem
            template={template}
            onAddToast={jest.fn()}
            detailUrl="/notification_templates/3/detail"
          />
        </tbody>
      </table>
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(NotificationTemplatesAPI.copy).toHaveBeenCalled();
    jest.clearAllMocks();
  });

  test('should render proper alert modal on copy error', async () => {
    NotificationTemplatesAPI.copy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/notification_templates/3/copy',
          },
          data: 'An error ocurred',
          status: 403,
        },
      })
    );

    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationTemplateListItem
            template={template}
            onAddToast={jest.fn()}
            detailUrl="/notification_templates/3/detail"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Modal').length).toBe(0);
    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(1);
    expect(wrapper.find('Modal').prop('isOpen')).toBe(true);
    jest.clearAllMocks();
  });

  test('should not render copy button', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <NotificationTemplateListItem
            template={{
              ...template,
              summary_fields: {
                organization: {
                  id: 3,
                  name: 'Test',
                },
                user_capabilities: {
                  copy: false,
                  edit: false,
                },
              },
            }}
            onAddToast={jest.fn()}
            detailUrl="/notification_templates/3/detail"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });
});
