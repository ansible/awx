import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { ConfigContext } from '../../../../src/context';
import OrganizationAdd from '../../../../src/pages/Organizations/screens/OrganizationAdd';

describe('<OrganizationAdd />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd
            match={{ path: '/organizations/add', url: '/organizations/add' }}
            location={{ search: '', pathname: '/organizations/add' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
  });
  test('calls "onFieldChange" when input values change', () => {
    const spy = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'onFieldChange');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd
            match={{ path: '/organizations/add', url: '/organizations/add' }}
            location={{ search: '', pathname: '/organizations/add' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('input#add-org-form-name').simulate('change', { target: { value: 'foo' } });
    wrapper.find('input#add-org-form-description').simulate('change', { target: { value: 'bar' } });
    expect(spy).toHaveBeenCalledTimes(2);
  });
  test('calls "onSubmit" when Save button is clicked', () => {
    const spy = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'onSubmit');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd
            match={{ path: '/organizations/add', url: '/organizations/add' }}
            location={{ search: '', pathname: '/organizations/add' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').prop('onClick')();
    expect(spy).toBeCalled();
  });
  test('calls "onCancel" when Cancel button is clicked', () => {
    const spy = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'onCancel');
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd
            match={{ path: '/organizations/add', url: '/organizations/add' }}
            location={{ search: '', pathname: '/organizations/add' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(spy).toBeCalled();
  });

  test('Successful form submission triggers redirect', (done) => {
    const onSuccess = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'onSuccess');
    const mockedResp = { data: { id: 1, related: { instance_groups: '/bar' } } };
    const api = { createOrganization: jest.fn().mockResolvedValue(mockedResp), createInstanceGroups: jest.fn().mockResolvedValue('done') };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd api={api} />
        </I18nProvider>
      </MemoryRouter>
    );
    wrapper.find('input#add-org-form-name').simulate('change', { target: { value: 'foo' } });
    wrapper.find('button[aria-label="Save"]').prop('onClick')();
    setImmediate(() => {
      expect(onSuccess).toHaveBeenCalled();
      done();
    });
  });

  test('onLookupSave successfully sets instanceGroups state', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd api={{}} />
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationAdd');
    wrapper.instance().onLookupSave([
      {
        id: 1,
        name: 'foo'
      }
    ], 'instanceGroups');
    expect(wrapper.state('instanceGroups')).toEqual([
      {
        id: 1,
        name: 'foo'
      }
    ]);
  });

  test('onFieldChange successfully sets custom_virtualenv state', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd api={{}} />
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationAdd');
    wrapper.instance().onFieldChange('fooBar', { target: { name: 'custom_virtualenv' } });
    expect(wrapper.state('custom_virtualenv')).toBe('fooBar');
  });

  test('onSubmit posts instance groups from selectedInstanceGroups', async () => {
    const createOrganizationFn = jest.fn().mockResolvedValue({
      data: {
        id: 1,
        name: 'mock org',
        related: {
          instance_groups: '/api/v2/organizations/1/instance_groups'
        }
      }
    });
    const createInstanceGroupsFn = jest.fn().mockResolvedValue('done');
    const api = {
      createOrganization: createOrganizationFn,
      createInstanceGroups: createInstanceGroupsFn
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <OrganizationAdd api={api} />
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationAdd');
    wrapper.setState({
      name: 'mock org',
      instanceGroups: [{
        id: 1,
        name: 'foo'
      }]
    });
    await wrapper.instance().onSubmit();
    expect(createOrganizationFn).toHaveBeenCalledWith({
      custom_virtualenv: '',
      description: '',
      name: 'mock org'
    });
    expect(createInstanceGroupsFn).toHaveBeenCalledWith('/api/v2/organizations/1/instance_groups', 1);
  });

  test('AnsibleSelect component renders if there are virtual environments', () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <ConfigContext.Provider value={config}>
            <OrganizationAdd api={{}} />
          </ConfigContext.Provider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationAdd').find('AnsibleSelect');
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(2);
  });

  test('AnsibleSelect component does not render if there are 0 virtual environments', () => {
    const config = {
      custom_virtualenvs: [],
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <ConfigContext.Provider value={config}>
            <OrganizationAdd api={{}} />
          </ConfigContext.Provider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationAdd').find('AnsibleSelect');
    expect(wrapper.find('FormSelect')).toHaveLength(0);
  });
});
