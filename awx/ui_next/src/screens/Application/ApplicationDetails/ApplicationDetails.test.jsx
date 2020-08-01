import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { ApplicationsAPI } from '../../../api';
import ApplicationDetails from './ApplicationDetails';

jest.mock('../../../api/models/Applications');

const application = {
  id: 10,
  type: 'o_auth2_application',
  url: '/api/v2/applications/10/',
  related: {
    named_url: '/api/v2/applications/Alex++bar/',
    tokens: '/api/v2/applications/10/tokens/',
    activity_stream: '/api/v2/applications/10/activity_stream/',
  },
  summary_fields: {
    organization: {
      id: 230,
      name: 'bar',
      description:
        'SaleNameBedPersonalityManagerWhileFinanceBreakToothPerson魲',
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
    tokens: {
      count: 2,
      results: [
        {
          id: 1,
          token: '************',
          scope: 'read',
        },
        {
          id: 2,
          token: '************',
          scope: 'write',
        },
      ],
    },
  },
  created: '2020-06-11T17:54:33.983993Z',
  modified: '2020-06-11T17:54:33.984039Z',
  name: 'Alex',
  description: 'foo',
  client_id: 'b1dmj8xzkbFm1ZQ27ygw2ZeE9I0AXqqeL74fiyk4',
  client_secret: '************',
  client_type: 'confidential',
  redirect_uris: 'http://www.google.com',
  authorization_grant_type: 'authorization-code',
  skip_authorization: false,
  organization: 230,
};

const authorizationOptions = [
  {
    key: 'authorization-code',
    label: 'Authorization code',
    value: 'authorization-code',
  },
  {
    key: 'password',
    label: 'Resource owner password-based',
    value: 'password',
  },
];

const clientTypeOptions = [
  { key: 'confidential', label: 'Confidential', value: 'confidential' },
  { key: 'public', label: 'Public', value: 'public' },
];

describe('<ApplicationDetails/>', () => {
  let wrapper;
  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationDetails
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(wrapper.find('ApplicationDetails').length).toBe(1);
  });

  test('should render proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationDetails
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(wrapper.find('Detail[label="Name"]').prop('value')).toBe('Alex');
    expect(wrapper.find('Detail[label="Description"]').prop('value')).toBe(
      'foo'
    );
    expect(wrapper.find('Detail[label="Organization"]').length).toBe(1);
    expect(
      wrapper
        .find('Link')
        .at(0)
        .prop('to')
    ).toBe('/organizations/230/details');
    expect(
      wrapper.find('Detail[label="Authorization grant type"]').prop('value')
    ).toBe('Authorization code');
    expect(wrapper.find('Detail[label="Redirect uris"]').prop('value')).toBe(
      'http://www.google.com'
    );
    expect(wrapper.find('Detail[label="Client type"]').prop('value')).toBe(
      'Confidential'
    );
    expect(wrapper.find('Button[aria-label="Edit"]').prop('to')).toBe(
      '/applications/10/edit'
    );
    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(1);
  });

  test('should delete properly', async () => {
    ApplicationsAPI.destroy.mockResolvedValue({ data: {} });
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationDetails
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();
    await act(async () => wrapper.find('DeleteButton').prop('onConfirm')());
    expect(ApplicationsAPI.destroy).toBeCalledWith(10);
  });

  test(' should not render delete button', async () => {
    application.summary_fields.user_capabilities.delete = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationDetails
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(0);
  });
  test(' should not render edit button', async () => {
    application.summary_fields.user_capabilities.edit = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationDetails
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(wrapper.find('Button[aria-label="Edit"]').length).toBe(0);
  });
});
