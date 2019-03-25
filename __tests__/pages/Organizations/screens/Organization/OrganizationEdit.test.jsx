import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { ConfigContext } from '../../../../../src/context';
import OrganizationEdit from '../../../../../src/pages/Organizations/screens/Organization/OrganizationEdit';

describe('<OrganizationEdit />', () => {
  let api;

  const mockData = {
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    id: 1,
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups'
    }
  };

  beforeEach(() => {
    api = {
      getInstanceGroups: jest.fn(),
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
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <OrganizationEdit
            match={{ params: { id: '1' } }}
            api={api}
            organization={mockData}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationEdit');

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
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <OrganizationEdit
            match={{
              path: '/organizations/:id',
              url: '/organizations/1',
              params: { id: '1' }
            }}
            organization={mockData}
            api={api}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationEdit');

    await wrapper.instance().componentDidMount();
    expect(wrapper.state().form.instanceGroups.value).toEqual(mockInstanceGroups);
  });

  test('changing instance group successfully sets instanceGroups state', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationEdit
            organization={mockData}
            api={api}
            match={{ path: '/organizations/:id/edit', url: '/organizations/1/edit' }}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationEdit');

    const lookup = wrapper.find('InstanceGroupsLookup');
    expect(lookup.length).toBe(1);

    lookup.prop('onChange')([
      {
        id: 1,
        name: 'foo'
      }
    ], 'instanceGroups');
    expect(wrapper.state().form.instanceGroups.value).toEqual([
      {
        id: 1,
        name: 'foo'
      }
    ]);
  });

  test('calls "handleFieldChange" when input values change', () => {
    const spy = jest.spyOn(OrganizationEdit.WrappedComponent.prototype, 'handleFieldChange');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationEdit
            organization={mockData}
            api={api}
            match={{ path: '/organizations/:id/edit', url: '/organizations/1/edit' }}
          />
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationEdit');

    expect(spy).not.toHaveBeenCalled();
    wrapper.instance().handleFieldChange('foo', { target: { name: 'name' } });
    wrapper.instance().handleFieldChange('bar', { target: { name: 'description' } });
    expect(spy).toHaveBeenCalledTimes(2);
  });

  test('AnsibleSelect component renders if there are virtual environments', () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <ConfigContext.Provider value={config}>
            <OrganizationEdit
              match={{
                path: '/organizations/:id',
                url: '/organizations/1',
                params: { id: '1' }
              }}
              organization={mockData}
              api={api}
            />
          </ConfigContext.Provider>
        </I18nProvider>
      </MemoryRouter>
    );
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(2);
  });

  test('calls handleSubmit when Save button is clicked', () => {
    const spy = jest.spyOn(OrganizationEdit.WrappedComponent.prototype, 'handleSubmit');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationEdit
            match={{
              path: '/organizations/:id',
              url: '/organizations/1',
              params: { id: '1' }
            }}
            organization={mockData}
            api={api}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').prop('onClick')();
    expect(spy).toBeCalled();
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
    api.updateOrganizationDetails = jest.fn().mockResolvedValue(1, mockDataForm);
    api.associateInstanceGroup = jest.fn().mockResolvedValue('done');
    api.disassociate = jest.fn().mockResolvedValue('done');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <OrganizationEdit
            match={{
              path: '/organizations/:id',
              url: '/organizations/1',
              params: { id: '1' }
            }}
            organization={mockData}
            api={api}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationEdit');

    await wrapper.instance().componentDidMount();

    wrapper.find('InstanceGroupsLookup').prop('onChange')([
      { name: 'One', id: 1 },
      { name: 'Three', id: 3 }
    ], 'instanceGroups');

    await wrapper.instance().handleSubmit();
    expect(api.updateOrganizationDetails).toHaveBeenCalledWith(1, mockDataForm);
    expect(api.associateInstanceGroup).toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 3);
    expect(api.associateInstanceGroup).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 1);
    expect(api.associateInstanceGroup).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 2);

    expect(api.disassociate).toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 2);
    expect(api.disassociate).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 1);
    expect(api.disassociate).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 3);
  });

  test('calls "handleCancel" when Cancel button is clicked', () => {
    const spy = jest.spyOn(OrganizationEdit.WrappedComponent.prototype, 'handleCancel');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationEdit
            match={{
              path: '/organizations/:id',
              url: '/organizations/1',
              params: { id: '1' }
            }}
            organization={mockData}
            api={api}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(spy).toBeCalled();
  });
});
