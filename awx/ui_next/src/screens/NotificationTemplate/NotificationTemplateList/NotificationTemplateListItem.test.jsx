import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { NotificationTemplatesAPI } from '../../../api';
import NotificationTemplateListItem from './NotificationTemplateListItem';

jest.mock('../../../api/models/NotificationTemplates');

const template = {
  id: 3,
  notification_type: 'slack',
  name: 'Test Notification',
  summary_fields: {
    user_capabilities: {
      edit: true,
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
      <NotificationTemplateListItem
        template={template}
        detailUrl="/notification_templates/3/detail"
      />
    );

    const cells = wrapper.find('DataListCell');
    expect(cells).toHaveLength(3);
    expect(cells.at(0).text()).toEqual('Test Notification');
    expect(cells.at(1).text()).toEqual('Success');
    expect(cells.at(2).text()).toEqual('Type: Slack');
  });

  test('should send test notification', async () => {
    NotificationTemplatesAPI.test.mockResolvedValue({
      data: { notification: 1 },
    });

    const wrapper = mountWithContexts(
      <NotificationTemplateListItem
        template={template}
        detailUrl="/notification_templates/3/detail"
      />
    );
    await act(async () => {
      wrapper
        .find('Button')
        .at(0)
        .invoke('onClick')();
    });
    expect(NotificationTemplatesAPI.test).toHaveBeenCalledTimes(1);
    expect(
      wrapper
        .find('DataListCell')
        .at(1)
        .text()
    ).toEqual('Running');
  });
});
