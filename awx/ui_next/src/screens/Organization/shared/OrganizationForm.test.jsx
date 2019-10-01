import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import { OrganizationsAPI } from '@api';

import OrganizationForm from './OrganizationForm';

jest.mock('@api');

describe('<OrganizationForm />', () => {
  const network = {};
  const meConfig = {
    me: {
      is_superuser: false,
    },
  };
  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    max_hosts: 1,
    custom_virtualenv: 'Fizz',
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups',
    },
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should request related instance groups from api', () => {
    mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />,
      {
        context: { network },
      }
    );

    expect(OrganizationsAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('componentDidMount should set instanceGroups to state', async () => {
    const mockInstanceGroups = [{ name: 'One', id: 1 }, { name: 'Two', id: 2 }];
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />,
      {
        context: { network },
      }
    );

    await sleep(0);
    expect(OrganizationsAPI.readInstanceGroups).toHaveBeenCalled();
    expect(wrapper.find('OrganizationForm').state().instanceGroups).toEqual(
      mockInstanceGroups
    );
  });

  test('changing instance group successfully sets instanceGroups state', () => {
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );

    const lookup = wrapper.find('InstanceGroupsLookup');
    expect(lookup.length).toBe(1);

    lookup.prop('onChange')(
      [
        {
          id: 1,
          name: 'foo',
        },
      ],
      'instanceGroups'
    );
    expect(wrapper.find('OrganizationForm').state().instanceGroups).toEqual([
      {
        id: 1,
        name: 'foo',
      },
    ]);
  });

  test('changing inputs should update form values', () => {
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );

    const form = wrapper.find('Formik');
    wrapper.find('input#org-name').simulate('change', {
      target: { value: 'new foo', name: 'name' },
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#org-description').simulate('change', {
      target: { value: 'new bar', name: 'description' },
    });
    expect(form.state('values').description).toEqual('new bar');
    wrapper.find('input#org-max_hosts').simulate('change', {
      target: { value: '134', name: 'max_hosts' },
    });
    expect(form.state('values').max_hosts).toEqual('134');
  });

  test('AnsibleSelect component renders if there are virtual environments', () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />,
      {
        context: { config },
      }
    );
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(3);
    expect(
      wrapper
        .find('FormSelectOption')
        .first()
        .prop('value')
    ).toEqual('/venv/ansible/');
  });

  test('calls handleSubmit when form submitted', async () => {
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );
    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toHaveBeenCalledWith(
      {
        name: 'Foo',
        description: 'Bar',
        max_hosts: 1,
        custom_virtualenv: 'Fizz',
      },
      [],
      []
    );
  });

  test('handleSubmit associates and disassociates instance groups', async () => {
    const mockInstanceGroups = [{ name: 'One', id: 1 }, { name: 'Two', id: 2 }];
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    const mockDataForm = {
      name: 'Foo',
      description: 'Bar',
      max_hosts: 1,
      custom_virtualenv: 'Fizz',
    };
    const handleSubmit = jest.fn();
    OrganizationsAPI.update.mockResolvedValue(1, mockDataForm);
    OrganizationsAPI.associateInstanceGroup.mockResolvedValue('done');
    OrganizationsAPI.disassociateInstanceGroup.mockResolvedValue('done');
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />,
      {
        context: { network },
      }
    );
    await sleep(0);
    wrapper.find('InstanceGroupsLookup').prop('onChange')(
      [{ name: 'One', id: 1 }, { name: 'Three', id: 3 }],
      'instanceGroups'
    );

    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);
    expect(handleSubmit).toHaveBeenCalledWith(mockDataForm, [3], [2]);
  });

  test('handleSubmit is called with max_hosts value if it is in range', async () => {
    const handleSubmit = jest.fn();

    // normal mount
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);
    expect(handleSubmit).toHaveBeenCalledWith(
      {
        name: 'Foo',
        description: 'Bar',
        max_hosts: 1,
        custom_virtualenv: 'Fizz',
      },
      [],
      []
    );
  });

  test('handleSubmit does not get called if max_hosts value is out of range', async () => {
    const handleSubmit = jest.fn();

    // not mount with Negative value
    const mockDataNegative = JSON.parse(JSON.stringify(mockData));
    mockDataNegative.max_hosts = -5;
    const wrapper1 = mountWithContexts(
      <OrganizationForm
        organization={mockDataNegative}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );
    wrapper1.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);
    expect(handleSubmit).not.toHaveBeenCalled();

    // not mount with Out of Range value
    const mockDataOoR = JSON.parse(JSON.stringify(mockData));
    mockDataOoR.max_hosts = 999999999999;
    const wrapper2 = mountWithContexts(
      <OrganizationForm
        organization={mockDataOoR}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );
    wrapper2.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  test('handleSubmit is called and max_hosts value defaults to 0 if input is not a number', async () => {
    const handleSubmit = jest.fn();

    // mount with String value (default to zero)
    const mockDataString = JSON.parse(JSON.stringify(mockData));
    mockDataString.max_hosts = 'Bee';
    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockDataString}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(0);
    expect(handleSubmit).toHaveBeenCalledWith(
      {
        name: 'Foo',
        description: 'Bar',
        max_hosts: 0,
        custom_virtualenv: 'Fizz',
      },
      [],
      []
    );
  });

  test('calls "handleCancel" when Cancel button is clicked', () => {
    const handleCancel = jest.fn();

    const wrapper = mountWithContexts(
      <OrganizationForm
        organization={mockData}
        handleSubmit={jest.fn()}
        handleCancel={handleCancel}
        me={meConfig.me}
      />
    );
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
