import React from 'react';
import { mountWithContexts } from '../../../enzymeHelpers';
import { sleep } from '../../../testUtils';
import OrganizationForm from '../../../../src/pages/Organizations/components/OrganizationForm';

describe('<OrganizationForm />', () => {
  let network;

  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups'
    }
  };

  beforeEach(() => {
    network = {};
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should request related instance groups from api', () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    network.api = {
      getOrganizationInstanceGroups: jest.fn(() => (
        Promise.resolve({ data: { results: mockInstanceGroups } })
      ))
    };
    mountWithContexts(
      (
        <OrganizationForm
          organization={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      ), {
        context: { network },
      }
    );

    expect(network.api.getOrganizationInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('componentDidMount should set instanceGroups to state', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    network.api = {
      getOrganizationInstanceGroups: jest.fn(() => (
        Promise.resolve({ data: { results: mockInstanceGroups } })
      ))
    };
    const wrapper = mountWithContexts(
      (
        <OrganizationForm
          organization={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      ), {
        context: { network },
      }
    );

    await sleep(0);
    expect(network.api.getOrganizationInstanceGroups).toHaveBeenCalled();
    expect(wrapper.find('OrganizationForm').state().instanceGroups).toEqual(mockInstanceGroups);
  });

  test('changing instance group successfully sets instanceGroups state', () => {
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );

    const lookup = wrapper.find('InstanceGroupsLookup');
    expect(lookup.length).toBe(1);

    lookup.prop('onChange')([
      {
        id: 1,
        name: 'foo'
      }
    ], 'instanceGroups');
    expect(wrapper.find('OrganizationForm').state().instanceGroups).toEqual([
      {
        id: 1,
        name: 'foo'
      }
    ]);
  });

  test('changing inputs should update form values', () => {
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );

    const form = wrapper.find('Formik');
    wrapper.find('input#org-name').simulate('change', {
      target: { value: 'new foo', name: 'name' }
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#org-description').simulate('change', {
      target: { value: 'new bar', name: 'description' }
    });
    expect(form.state('values').description).toEqual('new bar');
  });

  test('AnsibleSelect component renders if there are virtual environments', () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    const wrapper = mountWithContexts(
      (
        <OrganizationForm
          organization={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
        />
      ), {
        context: { config },
      }
    );
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(2);
  });

  test('calls handleSubmit when form submitted', async () => {
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
      />
    );
    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toHaveBeenCalledWith({
      name: 'Foo',
      description: 'Bar',
      custom_virtualenv: 'Fizz',
    }, [], []);
  });

  test('handleSubmit associates and disassociates instance groups', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 }
    ];
    network.api = {
      getOrganizationInstanceGroups: jest.fn(() => (
        Promise.resolve({ data: { results: mockInstanceGroups } })
      ))
    };
    const mockDataForm = {
      name: 'Foo',
      description: 'Bar',
      custom_virtualenv: 'Fizz',
    };
    const handleSubmit = jest.fn();
    network.api.updateOrganizationDetails = jest.fn().mockResolvedValue(1, mockDataForm);
    network.api.associateInstanceGroup = jest.fn().mockResolvedValue('done');
    network.api.disassociate = jest.fn().mockResolvedValue('done');
    const wrapper = mountWithContexts(
      (
        <OrganizationForm
          organization={mockData}
          handleSubmit={handleSubmit}
          handleCancel={jest.fn()}
        />
      ), {
        context: { network },
      }
    );

    await sleep(0);

    wrapper.find('InstanceGroupsLookup').prop('onChange')([
      { name: 'One', id: 1 },
      { name: 'Three', id: 3 }
    ], 'instanceGroups');

    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);
    expect(handleSubmit).toHaveBeenCalledWith(mockDataForm, [3], [2]);
  });

  test('calls "handleCancel" when Cancel button is clicked', () => {
    const handleCancel = jest.fn();
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={handleCancel}
      />
    );
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
