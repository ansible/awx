import React from 'react';
import { mount } from 'enzyme';
import OrganizationAdd from '../../../../src/pages/Organizations/views/Organization.add';
import { MemoryRouter } from 'react-router-dom';

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
});
