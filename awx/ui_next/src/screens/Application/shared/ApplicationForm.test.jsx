import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { OrganizationsAPI } from '../../../api';
import ApplicationForm from './ApplicationForm';

jest.mock('../../../api');

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

describe('<ApplicationForm', () => {
  let wrapper;
  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationForm
          onSubmit={() => {}}
          application={{}}
          onCancel={() => {}}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(wrapper.find('ApplicationForm').length).toBe(1);
  });

  test('all fields should render successsfully', async () => {
    OrganizationsAPI.read.mockResolvedValue({
      results: [{ id: 1 }, { id: 2 }],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationForm
          onSubmit={() => {}}
          application={{}}
          onCancel={() => {}}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(wrapper.find('input#name').length).toBe(1);
    expect(wrapper.find('input#description').length).toBe(1);
    expect(
      wrapper.find('AnsibleSelect[name="authorization_grant_type"]').length
    ).toBe(1);
    expect(wrapper.find('input#redirect_uris').length).toBe(1);
    expect(wrapper.find('AnsibleSelect[name="client_type"]').length).toBe(1);
    expect(wrapper.find('OrganizationLookup').length).toBe(1);
  });

  test('should update field values', async () => {
    OrganizationsAPI.read.mockResolvedValue({
      results: [{ id: 1 }, { id: 2 }],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationForm
          onSubmit={() => {}}
          application={{}}
          onCancel={() => {}}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
      await act(async () => {
        wrapper.find('input#name').simulate('change', {
          target: { value: 'new foo', name: 'name' },
        });
        wrapper.find('input#description').simulate('change', {
          target: { value: 'new bar', name: 'description' },
        });
        wrapper
          .find('AnsibleSelect[name="authorization_grant_type"]')
          .prop('onChange')({}, 'authorization-code');

        wrapper.find('input#redirect_uris').simulate('change', {
          target: { value: 'https://www.google.com', name: 'redirect_uris' },
        });
        wrapper.find('AnsibleSelect[name="client_type"]').prop('onChange')(
          {},
          'confidential'
        );
        wrapper.find('OrganizationLookup').invoke('onChange')({
          id: 3,
          name: 'organization',
        });
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
    expect(
      wrapper.find('FormField[label="Redirect URIs"]').prop('isRequired')
    ).toBe(true);
    expect(wrapper.find('input#redirect_uris').prop('value')).toBe(
      'https://www.google.com'
    );
  });
  test('should call onCancel', async () => {
    OrganizationsAPI.read.mockResolvedValue({
      results: [{ id: 1 }, { id: 2 }],
    });
    const onSubmit = jest.fn();
    const onCancel = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationForm
          onSubmit={onSubmit}
          application={{}}
          onCancel={onCancel}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    wrapper.find('Button[aria-label="Cancel"]').prop('onClick')();
    expect(onCancel).toBeCalled();
  });
  test('should call onSubmit', async () => {
    OrganizationsAPI.read.mockResolvedValue({
      results: [{ id: 1 }, { id: 2 }],
    });
    const onSubmit = jest.fn();
    const onCancel = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationForm
          onSubmit={onSubmit}
          application={{}}
          onCancel={onCancel}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    wrapper.find('Formik').prop('onSubmit')({
      authorization_grant_type: 'authorization-code',
      client_type: 'confidential',
      description: 'bar',
      name: 'foo',
      organization: 1,
      redirect_uris: 'http://www.google.com',
    });
    expect(onSubmit).toBeCalledWith({
      authorization_grant_type: 'authorization-code',
      client_type: 'confidential',
      description: 'bar',
      name: 'foo',
      organization: 1,
      redirect_uris: 'http://www.google.com',
    });
  });
  test('should render required on Redirect URIs', async () => {
    OrganizationsAPI.read.mockResolvedValue({
      results: [{ id: 1 }, { id: 2 }],
    });
    const onSubmit = jest.fn();
    const onCancel = jest.fn();
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
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationForm
          onSubmit={onSubmit}
          application={application}
          onCancel={onCancel}
          authorizationOptions={authorizationOptions}
          clientTypeOptions={clientTypeOptions}
        />
      );
    });
    expect(
      wrapper.find('FormField[name="redirect_uris"]').prop('isRequired')
    ).toBe(true);
  });
});
