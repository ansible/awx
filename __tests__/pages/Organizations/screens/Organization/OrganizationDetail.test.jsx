import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import OrganizationDetail from '../../../../../src/pages/Organizations/screens/Organization/OrganizationDetail';

describe('<OrganizationDetail />', () => {
  const mockDetails = {
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    created: 'Bat',
    modified: 'Boo',
    summary_fields: {
      user_capabilities: {
        edit: true
      }
    }
  };

  test('initially renders succesfully', () => {
    mountWithContexts(
      <OrganizationDetail
        organization={mockDetails}
      />
    );
  });

  test('should request instance groups from api', () => {
    const getOrganizationInstanceGroups = jest.fn();
    mountWithContexts(
      <OrganizationDetail
        organization={mockDetails}
      />, { context: {
        network: { api: { getOrganizationInstanceGroups }, handleHttpError: () => {} }
      } }
    ).find('OrganizationDetail');

    expect(getOrganizationInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('should handle setting instance groups to state', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    const getOrganizationInstanceGroups = jest.fn(() => (
      Promise.resolve({ data: { results: mockInstanceGroups } })
    ));
    const wrapper = mountWithContexts(
      <OrganizationDetail
        organization={mockDetails}
      />, { context: {
        network: { api: { getOrganizationInstanceGroups }, handleHttpError: () => {} }
      } }
    ).find('OrganizationDetail');

    await getOrganizationInstanceGroups();
    expect(wrapper.state().instanceGroups).toEqual(mockInstanceGroups);
  });

  test('should render Details', async () => {
    const wrapper = mountWithContexts(
      <OrganizationDetail
        organization={mockDetails}
      />
    );

    const detailWrapper = wrapper.find('Detail');
    expect(detailWrapper.length).toBe(5);

    const nameDetail = detailWrapper.findWhere(node => node.props().label === 'Name');
    const descriptionDetail = detailWrapper.findWhere(node => node.props().label === 'Description');
    const custom_virtualenvDetail = detailWrapper.findWhere(node => node.props().label === 'Ansible Environment');
    const createdDetail = detailWrapper.findWhere(node => node.props().label === 'Created');
    const modifiedDetail = detailWrapper.findWhere(node => node.props().label === 'Last Modified');
    expect(nameDetail.find('dt').text()).toBe('Name');
    expect(nameDetail.find('dd').text()).toBe('Foo');

    expect(descriptionDetail.find('dt').text()).toBe('Description');
    expect(descriptionDetail.find('dd').text()).toBe('Bar');

    expect(custom_virtualenvDetail.find('dt').text()).toBe('Ansible Environment');
    expect(custom_virtualenvDetail.find('dd').text()).toBe('Fizz');

    expect(createdDetail.find('dt').text()).toBe('Created');
    expect(createdDetail.find('dd').text()).toBe('Bat');

    expect(modifiedDetail.find('dt').text()).toBe('Last Modified');
    expect(modifiedDetail.find('dd').text()).toBe('Boo');
  });

  test('should show edit button for users with edit permission', () => {
    const wrapper = mountWithContexts(
      <OrganizationDetail
        organization={mockDetails}
      />
    ).find('OrganizationDetail');
    const editButton = wrapper.find('Button');
    expect((editButton).prop('to')).toBe('/organizations/undefined/edit');
  });

  test('should hide edit button for users without edit permission', () => {
    const readOnlyOrg = { ...mockDetails };
    readOnlyOrg.summary_fields.user_capabilities.edit = false;
    const wrapper = mountWithContexts(
      <OrganizationDetail
        organization={readOnlyOrg}
      />
    ).find('OrganizationDetail');

    const editLink = wrapper.findWhere(node => node.props().to === '/organizations/undefined/edit');
    expect(editLink.length).toBe(0);
  });
});
