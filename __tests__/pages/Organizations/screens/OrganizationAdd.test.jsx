import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import OrganizationAdd from '../../../../src/pages/Organizations/screens/OrganizationAdd';

describe('<OrganizationAdd />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter>
        <OrganizationAdd
          match={{ path: '/organizations/add', url: '/organizations/add' }}
          location={{ search: '', pathname: '/organizations/add' }}
        />
      </MemoryRouter>
    );
  });
  test('calls "handleChange" when input values change', () => {
    const spy = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'handleChange');
    const wrapper = mount(
      <MemoryRouter>
        <OrganizationAdd
          match={{ path: '/organizations/add', url: '/organizations/add' }}
          location={{ search: '', pathname: '/organizations/add' }}
        />
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
        <OrganizationAdd
          match={{ path: '/organizations/add', url: '/organizations/add' }}
          location={{ search: '', pathname: '/organizations/add' }}
        />
      </MemoryRouter>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('button.at-C-SubmitButton').prop('onClick')();
    expect(spy).toBeCalled();
  });
  test('calls "onCancel" when Cancel button is clicked', () => {
    const spy = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'onCancel');
    const wrapper = mount(
      <MemoryRouter>
        <OrganizationAdd
          match={{ path: '/organizations/add', url: '/organizations/add' }}
          location={{ search: '', pathname: '/organizations/add' }}
        />
      </MemoryRouter>
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('button.at-C-CancelButton').prop('onClick')();
    expect(spy).toBeCalled();
  });

  test('API response is formatted properly', (done) => {
    const mockedResp = { data: { results: [{ name: 'test instance', id: 1 }] } };
    const api = { getInstanceGroups: jest.fn().mockResolvedValue(mockedResp) };
    const wrapper = mount(
      <MemoryRouter>
        <OrganizationAdd api={api} />
      </MemoryRouter>
    );

    setImmediate(() => {
      const orgAddElem = wrapper.find('OrganizationAdd');
      expect([{ id: 1, isChecked: false, name: 'test instance' }]).toEqual(orgAddElem.state().results);
      done();
    });
  });

  test('Successful form submission triggers redirect', (done) => {
    const onSuccess = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'onSuccess');
    const resetForm = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'resetForm');
    const mockedResp = { data: { id: 1, related: { instance_groups: '/bar' } } };
    const api = { createOrganization: jest.fn().mockResolvedValue(mockedResp), createInstanceGroups: jest.fn().mockResolvedValue('done') };
    const wrapper = mount(
      <MemoryRouter>
        <OrganizationAdd api={api} />
      </MemoryRouter>
    );
    wrapper.find('input#add-org-form-name').simulate('change', { target: { value: 'foo' } });
    wrapper.find('button.at-C-SubmitButton').prop('onClick')();
    setImmediate(() => {
      expect(onSuccess).toHaveBeenCalled();
      expect(resetForm).toHaveBeenCalled();
      done();
    });
  });

  test('updateSelectedInstanceGroups successfully sets selectedInstanceGroups state', () => {
    const wrapper = mount(
      <MemoryRouter>
        <OrganizationAdd api={{}} />
      </MemoryRouter>
    ).find('OrganizationAdd');
    wrapper.instance().updateSelectedInstanceGroups([
      {
        id: 1,
        name: 'foo'
      }
    ]);
    expect(wrapper.state('selectedInstanceGroups')).toEqual([
      {
        id: 1,
        name: 'foo'
      }
    ]);
  });

  test('onSelectChange successfully sets custom_virtualenv state', () => {
    const wrapper = mount(
      <MemoryRouter>
        <OrganizationAdd api={{}} />
      </MemoryRouter>
    ).find('OrganizationAdd');
    wrapper.instance().onSelectChange('foobar');
    expect(wrapper.state('custom_virtualenv')).toBe('foobar');
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
        <OrganizationAdd api={api} />
      </MemoryRouter>
    ).find('OrganizationAdd');
    wrapper.setState({
      name: 'mock org',
      selectedInstanceGroups: [{
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
});
