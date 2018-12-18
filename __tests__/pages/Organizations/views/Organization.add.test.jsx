import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';

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
