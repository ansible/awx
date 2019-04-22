import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import OrganizationDetail from '../../../../../src/pages/Organizations/screens/Organization/OrganizationDetail';

describe('<OrganizationDetail />', () => {
  const mockDetails = {
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    created: 'Bat',
    modified: 'Boo'
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

    expect(nameDetail.find('h6').text()).toBe('Name');
    expect(nameDetail.find('p').text()).toBe('Foo');

    expect(descriptionDetail.find('h6').text()).toBe('Description');
    expect(descriptionDetail.find('p').text()).toBe('Bar');

    expect(custom_virtualenvDetail.find('h6').text()).toBe('Ansible Environment');
    expect(custom_virtualenvDetail.find('p').text()).toBe('Fizz');

    expect(createdDetail.find('h6').text()).toBe('Created');
    expect(createdDetail.find('p').text()).toBe('Bat');

    expect(modifiedDetail.find('h6').text()).toBe('Last Modified');
    expect(modifiedDetail.find('p').text()).toBe('Boo');
  });
});
