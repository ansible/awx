import React from 'react';
import { act } from 'react-dom/test-utils';

import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import { ApplicationsAPI } from '../../../api';
import ApplicationEdit from './ApplicationEdit';

jest.mock('../../../api/models/Applications');
jest.mock('../../../api/models/Organizations');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  history: () => ({
    location: '/applications/1/edit',
  }),
  useParams: () => ({ id: 1 }),
}));

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

const application = {
  id: 1,
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
      count: 0,
      results: [],
    },
  },
  created: '2020-06-11T17:54:33.983993Z',
  modified: '2020-06-11T17:54:33.984039Z',
  name: 'Alex',
  description: '',
  client_id: 'b1dmj8xzkbFm1ZQ27ygw2ZeE9I0AXqqeL74fiyk4',
  client_secret: '************',
  client_type: 'confidential',
  redirect_uris: 'http://www.google.com',
  authorization_grant_type: 'authorization-code',
  skip_authorization: false,
  organization: 230,
};

describe('<ApplicationEdit/>', () => {
  let wrapper;
  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationEdit
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(wrapper.find('ApplicationEdit').length).toBe(1);
  });
  test('should cancel form properly', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/applications/1/edit'],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationEdit
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />,
        {
          context: { router: { history } },
        }
      );
      await act(async () => {
        wrapper.find('Button[aria-label="Cancel"]').prop('onClick')();
      });
      expect(history.location.pathname).toBe('/applications/1/details');
    });
  });
  test('should throw error on submit', async () => {
    const error = {
      response: {
        config: {
          method: 'patch',
          url: '/api/v2/applications/',
        },
        data: { detail: 'An error occurred' },
      },
    };
    ApplicationsAPI.update.mockRejectedValue(error);
    const history = createMemoryHistory({
      initialEntries: ['/applications/1/edit'],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationEdit
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />,
        {
          context: { router: { history } },
        }
      );
    });
    await act(async () => {
      wrapper.find('Formik').prop('onSubmit')({
        id: 1,
        organization: { id: 4 },
      });
    });

    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
  test('expect values to be updated and submitted properly', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/applications/1/edit'],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationEdit
          application={application}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />,
        {
          context: { router: { history } },
        }
      );
    });
    await act(async () => {
      wrapper.find('input#name').simulate('change', {
        target: { value: 'new foo', name: 'name' },
      });
      wrapper.find('input#description').simulate('change', {
        target: { value: 'new bar', name: 'description' },
      });

      wrapper.find('input#redirect_uris').simulate('change', {
        target: { value: 'https://www.google.com', name: 'redirect_uris' },
      });
      wrapper.find('AnsibleSelect[name="client_type"]').prop('onChange')(
        {},
        'confidential'
      );
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 1,
        name: 'organization',
      });
    });

    wrapper.update();
    expect(wrapper.find('input#name').prop('value')).toBe('new foo');
    expect(wrapper.find('input#description').prop('value')).toBe('new bar');
    expect(wrapper.find('Chip').length).toBe(1);
    expect(wrapper.find('Chip').text()).toBe('organization');
    expect(
      wrapper
        .find('AnsibleSelect[name="authorization_grant_type"]')
        .prop('value')
    ).toBe('authorization-code');
    expect(
      wrapper.find('AnsibleSelect[name="client_type"]').prop('value')
    ).toBe('confidential');
    expect(wrapper.find('input#redirect_uris').prop('value')).toBe(
      'https://www.google.com'
    );
    await act(async () => {
      wrapper.find('Formik').prop('onSubmit')({
        authorization_grant_type: 'authorization-code',
        client_type: 'confidential',
        description: 'bar',
        name: 'foo',
        organization: { id: 1 },
        redirect_uris: 'http://www.google.com',
      });
    });

    expect(ApplicationsAPI.update).toBeCalledWith(1, {
      authorization_grant_type: 'authorization-code',
      client_type: 'confidential',
      description: 'bar',
      name: 'foo',
      organization: 1,
      redirect_uris: 'http://www.google.com',
    });
  });
});
