import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { ConfigContext } from '../../../../../src/context';
import APIClient from '../../../../../src/api';
import OrganizationEdit from '../../../../../src/pages/Organizations/screens/Organization/OrganizationEdit';

describe('<OrganizationEdit />', () => {
  const mockData = {
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    id: 1,
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups'
    }
  };

  test('should request related instance groups from api', () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    const getOrganizationInstanceGroups = jest.fn(() => (
      Promise.resolve({ data: { results: mockInstanceGroups } })
    ));
    mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <OrganizationEdit
            match={{ params: { id: '1' } }}
            api={{
              getOrganizationInstanceGroups
            }}
            organization={mockData}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationEdit');

    expect(getOrganizationInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('componentDidMount should set instanceGroups to state', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    const getOrganizationInstanceGroups = jest.fn(() => (
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
            api={{ getOrganizationInstanceGroups }}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationEdit');

    await wrapper.instance().componentDidMount();
    expect(wrapper.state().form.instanceGroups.value).toEqual(mockInstanceGroups);
  });
  test('onLookupSave successfully sets instanceGroups state', () => {
    const api = jest.fn();
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

    wrapper.instance().onLookupSave([
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
  test('calls "onFieldChange" when input values change', () => {
    const api = new APIClient();
    const spy = jest.spyOn(OrganizationEdit.WrappedComponent.prototype, 'onFieldChange');
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
    wrapper.instance().onFieldChange('foo', { target: { name: 'name' } });
    wrapper.instance().onFieldChange('bar', { target: { name: 'description' } });
    expect(spy).toHaveBeenCalledTimes(2);
  });
  test('AnsibleSelect component renders if there are virtual environments', () => {
    const api = jest.fn();
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
  test('calls onSubmit when Save button is clicked', () => {
    const api = jest.fn();
    const spy = jest.spyOn(OrganizationEdit.WrappedComponent.prototype, 'onSubmit');
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
  test('onSubmit associates and disassociates instance groups', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    const getOrganizationInstanceGroupsFn = jest.fn(() => (
      Promise.resolve({ data: { results: mockInstanceGroups } })
    ));
    const mockDataForm = {
      name: 'Foo',
      description: 'Bar',
      custom_virtualenv: 'Fizz',
    };
    const updateOrganizationDetailsFn = jest.fn().mockResolvedValue(1, mockDataForm);
    const associateInstanceGroupFn = jest.fn().mockResolvedValue('done');
    const disassociateInstanceGroupFn = jest.fn().mockResolvedValue('done');
    const api = {
      getOrganizationInstanceGroups: getOrganizationInstanceGroupsFn,
      updateOrganizationDetails: updateOrganizationDetailsFn,
      associateInstanceGroup: associateInstanceGroupFn,
      disassociate: disassociateInstanceGroupFn
    };
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

    wrapper.instance().onLookupSave([
      { name: 'One', id: 1 },
      { name: 'Three', id: 3 }
    ], 'instanceGroups');

    await wrapper.instance().onSubmit();
    expect(updateOrganizationDetailsFn).toHaveBeenCalledWith(1, mockDataForm);
    expect(associateInstanceGroupFn).toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 3);
    expect(associateInstanceGroupFn).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 1);
    expect(associateInstanceGroupFn).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 2);

    expect(disassociateInstanceGroupFn).toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 2);
    expect(disassociateInstanceGroupFn).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 1);
    expect(disassociateInstanceGroupFn).not.toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 3);
  });

  test('calls "onCancel" when Cancel button is clicked', () => {
    const api = jest.fn();
    const spy = jest.spyOn(OrganizationEdit.WrappedComponent.prototype, 'onCancel');
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
