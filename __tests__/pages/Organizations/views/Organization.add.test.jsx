import React from 'react';
import { mount } from 'enzyme';
import OrganizationAdd from '../../../../src/pages/Organizations/views/Organization.add';

describe('<OrganizationAdd />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationAdd
        match={{ path: '/organizations/add', url: '/organizations/add' }}
        location={{ search: '', pathname: '/organizations/add' }}
      />
    );
  });
  test('calls "onSelectChange" on dropdown select change', () => {
    const spy = jest.spyOn(OrganizationAdd.prototype, 'onSelectChange');
    const wrapper = mount(
      <OrganizationAdd
        match={{ path: '/organizations/add', url: '/organizations/add' }}
        location={{ search: '', pathname: '/organizations/add' }}
      />
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('select').simulate('change');
    expect(spy).toHaveBeenCalled();
  });
  test('calls "handleChange" when input values change', () => {
    const spy = jest.spyOn(OrganizationAdd.prototype, 'handleChange');
    const wrapper = mount(
      <OrganizationAdd
        match={{ path: '/organizations/add', url: '/organizations/add' }}
        location={{ search: '', pathname: '/organizations/add' }}
      />
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('input#add-org-form-name').simulate('change', {target: {value: 'foo'}});
    wrapper.find('input#add-org-form-description').simulate('change', {target: {value: 'bar'}});
    expect(spy).toHaveBeenCalledTimes(2);
  });
  test('calls "onSubmit" when Save button is clicked', () => {
    const spy = jest.spyOn(OrganizationAdd.prototype, 'onSubmit');
    const wrapper = mount(
      <OrganizationAdd
        match={{ path: '/organizations/add', url: '/organizations/add' }}
        location={{ search: '', pathname: '/organizations/add' }}
      />
    );
    expect(spy).not.toHaveBeenCalled();
    wrapper.find('button.at-C-SubmitButton').prop('onClick')();
    expect(spy).toBeCalled();
  });
});
