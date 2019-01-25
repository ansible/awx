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
});
