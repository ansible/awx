import React from 'react';
import { mount } from 'enzyme';

let OrganizationAdd;
const getAppWithConfigContext = (context = {
  custom_virtualenvs: ['foo', 'bar']
}) => {

  // Mock the ConfigContext module being used in our OrganizationAdd component
  jest.doMock('../../../../src/context', () => {
    return {
      ConfigContext: {
        Consumer: (props) => props.children(context)
      }
    }
  });

  // Return the updated OrganizationAdd module with mocked context
  return require('../../../../src/pages/Organizations/views/Organization.add').default;
};

beforeEach(() => {
  OrganizationAdd = getAppWithConfigContext();
})

describe('<OrganizationAdd />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationAdd
        match={{ path: '/organizations/add', url: '/organizations/add' }}
        location={{ search: '', pathname: '/organizations/add' }}
      />
    );
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
    wrapper.find('input#add-org-form-name').simulate('change', { target: { value: 'foo' } });
    wrapper.find('input#add-org-form-description').simulate('change', { target: { value: 'bar' } });
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
