import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import NotificationTemplateDetail from './NotificationTemplateDetail';
import defaultMessages from '../shared/notification-template-default-messages.json';

jest.mock('../../../api');

const mockTemplate = {
  id: 1,
  type: 'notification_template',
  url: '/api/v2/notification_templates/1/',
  related: {
    named_url: '/api/v2/notification_templates/abc++Default/',
    created_by: '/api/v2/users/2/',
    modified_by: '/api/v2/users/2/',
    test: '/api/v2/notification_templates/1/test/',
    notifications: '/api/v2/notification_templates/1/notifications/',
    copy: '/api/v2/notification_templates/1/copy/',
    organization: '/api/v2/organizations/1/',
  },
  summary_fields: {
    organization: {
      id: 1,
      name: 'Default',
      description: '',
    },
    created_by: {
      id: 2,
      username: 'test',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 2,
      username: 'test',
      first_name: '',
      last_name: '',
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
    },
    recent_notifications: [{ status: 'success' }],
  },
  created: '2021-06-16T18:52:23.811374Z',
  modified: '2021-06-16T18:53:37.631371Z',
  name: 'abc',
  description: 'foo description',
  organization: 1,
  notification_type: 'email',
  notification_configuration: {
    username: '',
    password: '',
    host: 'https://localhost',
    recipients: ['foo@ansible.com'],
    sender: 'bar@ansible.com',
    port: 324,
    timeout: 11,
    use_ssl: true,
    use_tls: true,
  },
  messages: null,
};

describe('<NotificationTemplateDetail />', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render Details', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <NotificationTemplateDetail
          template={mockTemplate}
          defaultMessages={defaultMessages}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }
    assertDetail('Name', mockTemplate.name);
    assertDetail('Description', mockTemplate.description);
    expect(
      wrapper
        .find('Detail[label="Email Options"]')
        .containsAllMatchingElements([<li>Use SSL</li>, <li>Use TLS</li>])
    ).toEqual(true);
    expect(
      wrapper.find('Detail[label="Email Options"]').prop('helpText')
    ).toBeDefined();
  });

  test('should render Details when defaultMessages is missing', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <NotificationTemplateDetail
          template={mockTemplate}
          defaultMessages={null}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }
    assertDetail('Name', mockTemplate.name);
    assertDetail('Description', mockTemplate.description);
    expect(
      wrapper
        .find('Detail[label="Email Options"]')
        .containsAllMatchingElements([<li>Use SSL</li>, <li>Use TLS</li>])
    ).toEqual(true);
    expect(
      wrapper.find('Detail[label="Email Options"]').prop('helpText')
    ).toBeDefined();
  });
});
