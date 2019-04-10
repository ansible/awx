import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
<<<<<<< HEAD
import { ConfigContext } from '../../../../src/context';
import OrganizationForm from '../../../../src/pages/Organizations/components/OrganizationForm';
import { sleep } from '../../../testUtils';
=======
import { ConfigProvider } from '../../../../src/contexts/Config';
import { NetworkProvider } from '../../../../src/contexts/Network';
import OrganizationForm, { _OrganizationForm } from '../../../../src/pages/Organizations/components/OrganizationForm';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
>>>>>>> fix unit tests for network handling

describe('<OrganizationForm />', () => {
  let api;
  let networkProviderValue;

  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups'
    }
  };

  beforeEach(() => {
    api = {
      getInstanceGroups: jest.fn(),
    };

    networkProviderValue = {
      api,
      handleHttpError: () => {}
    };
  });

  test('should request related instance groups from api', () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    api.getOrganizationInstanceGroups = jest.fn(() => (
      Promise.resolve({ data: { results: mockInstanceGroups } })
    ));
    mount(
      <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <_OrganizationForm
              api={api}
              organization={mockData}
              handleSubmit={jest.fn()}
              handleCancel={jest.fn()}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationForm');

    expect(api.getOrganizationInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('componentDidMount should set instanceGroups to state', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    api.getOrganizationInstanceGroups = jest.fn(() => (
      Promise.resolve({ data: { results: mockInstanceGroups } })
    ));
    const wrapper = mount(
      <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <_OrganizationForm
              organization={mockData}
              api={api}
              handleSubmit={jest.fn()}
              handleCancel={jest.fn()}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationForm');

    await wrapper.instance().componentDidMount();
    expect(wrapper.state().instanceGroups).toEqual(mockInstanceGroups);
  });

  test('changing instance group successfully sets instanceGroups state', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <OrganizationForm
              organization={mockData}
              handleSubmit={jest.fn()}
              handleCancel={jest.fn()}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationForm');

    const lookup = wrapper.find('InstanceGroupsLookup');
    expect(lookup.length).toBe(1);

    lookup.prop('onChange')([
      {
        id: 1,
        name: 'foo'
      }
    ], 'instanceGroups');
    expect(wrapper.state().instanceGroups).toEqual([
      {
        id: 1,
        name: 'foo'
      }
    ]);
  });

  test('changing inputs should update form values', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <OrganizationForm
              organization={mockData}
              handleSubmit={jest.fn()}
              handleCancel={jest.fn()}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationForm');

    const form = wrapper.find('Formik');
    wrapper.find('input#org-name').simulate('change', {
      target: { value: 'new foo', name: 'name' }
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#org-description').simulate('change', {
      target: { value: 'new bar', name: 'description' }
    });
    expect(form.state('values').description).toEqual('new bar');
  });

  test('AnsibleSelect component renders if there are virtual environments', () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider value={config}>
              <OrganizationForm
                organization={mockData}
                handleSubmit={jest.fn()}
                handleCancel={jest.fn()}
              />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(2);
  });

  test('calls handleSubmit when form submitted', async () => {
    const handleSubmit = jest.fn();
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <OrganizationForm
              organization={mockData}
              api={api}
              handleSubmit={handleSubmit}
              handleCancel={jest.fn()}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationForm');
    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toHaveBeenCalledWith({
      name: 'Foo',
      description: 'Bar',
      custom_virtualenv: 'Fizz',
    }, [], []);
  });

  test('handleSubmit associates and disassociates instance groups', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    api.getOrganizationInstanceGroups = jest.fn(() => (
      Promise.resolve({ data: { results: mockInstanceGroups } })
    ));
    const mockDataForm = {
      name: 'Foo',
      description: 'Bar',
      custom_virtualenv: 'Fizz',
    };
    const handleSubmit = jest.fn();
    api.updateOrganizationDetails = jest.fn().mockResolvedValue(1, mockDataForm);
    api.associateInstanceGroup = jest.fn().mockResolvedValue('done');
    api.disassociate = jest.fn().mockResolvedValue('done');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <NetworkProvider value={networkProviderValue}>
            <_OrganizationForm
              organization={mockData}
              api={api}
              handleSubmit={handleSubmit}
              handleCancel={jest.fn()}
            />
          </NetworkProvider>
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationForm');

    await wrapper.instance().componentDidMount();

    wrapper.find('InstanceGroupsLookup').prop('onChange')([
      { name: 'One', id: 1 },
      { name: 'Three', id: 3 }
    ], 'instanceGroups');

    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);
    expect(handleSubmit).toHaveBeenCalledWith(mockDataForm, [3], [2]);
  });

  test('calls "handleCancel" when Cancel button is clicked', () => {
    const handleCancel = jest.fn();
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <OrganizationForm
              organization={mockData}
              handleSubmit={jest.fn()}
              handleCancel={handleCancel}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
