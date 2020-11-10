import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { OrganizationsAPI } from '../../../api';

import OrganizationForm from './OrganizationForm';

jest.mock('../../../api');

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
  const mockInstanceGroups = [
    { name: 'One', id: 1 },
    { name: 'Two', id: 2 },
  ];

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should request related instance groups from api', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockData}
          onSubmit={jest.fn()}
          onCancel={jest.fn()}
          me={meConfig.me}
        />,
        {
          context: { network },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(OrganizationsAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('componentDidMount should set instanceGroups to state', async () => {
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockData}
          onSubmit={jest.fn()}
          onCancel={jest.fn()}
          me={meConfig.me}
        />,
        {
          context: { network },
        }
      );
    });

    await waitForElement(
      wrapper,
      'InstanceGroupsLookup',
      el => el.length === 1
    );
    expect(OrganizationsAPI.readInstanceGroups).toHaveBeenCalled();
    expect(wrapper.find('InstanceGroupsLookup Chip span')).toHaveLength(2);
  });

  test('Instance group is rendered when added', async () => {
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: { results: [] },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockData}
          onSubmit={jest.fn()}
          onCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });
    const lookup = await waitForElement(
      wrapper,
      'InstanceGroupsLookup',
      el => el.length === 1
    );
    expect(lookup.length).toBe(1);
    expect(lookup.find('Chip span')).toHaveLength(0);
    await act(async () => {
      lookup.prop('onChange')(
        [
          {
            id: 1,
            name: 'foo',
          },
        ],
        'instanceGroups'
      );
    });
    const group = await waitForElement(
      wrapper,
      'InstanceGroupsLookup Chip span',
      el => el.length === 1
    );
    expect(group.text()).toEqual('foo');
  });

  test('changing inputs and saving triggers expected callback', async () => {
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    let wrapper;
    const onSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockData}
          onSubmit={onSubmit}
          onCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('input#org-name').simulate('change', {
        target: { value: 'new foo', name: 'name' },
      });
      wrapper.find('input#org-description').simulate('change', {
        target: { value: 'new bar', name: 'description' },
      });
      wrapper.find('input#org-max_hosts').simulate('change', {
        target: { value: 134, name: 'max_hosts' },
      });
    });
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toEqual({
      name: 'new foo',
      description: 'new bar',
      galaxy_credentials: [],
      custom_virtualenv: 'Fizz',
      max_hosts: 134,
    });
  });

  test('AnsibleSelect component renders if there are virtual environments', async () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockData}
          onSubmit={jest.fn()}
          onCancel={jest.fn()}
          me={meConfig.me}
        />,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(3);
    expect(
      wrapper
        .find('FormSelectOption')
        .first()
        .prop('value')
    ).toEqual('/venv/ansible/');
  });

  test('onSubmit associates and disassociates instance groups', async () => {
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    const mockDataForm = {
      name: 'Foo',
      description: 'Bar',
      galaxy_credentials: [],
      max_hosts: 1,
      custom_virtualenv: 'Fizz',
    };
    const onSubmit = jest.fn();
    OrganizationsAPI.update.mockResolvedValue(1, mockDataForm);
    OrganizationsAPI.associateInstanceGroup.mockResolvedValue('done');
    OrganizationsAPI.disassociateInstanceGroup.mockResolvedValue('done');
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockData}
          onSubmit={onSubmit}
          onCancel={jest.fn()}
          me={meConfig.me}
        />,
        {
          context: { network },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('InstanceGroupsLookup').prop('onChange')(
        [
          { name: 'One', id: 1 },
          { name: 'Three', id: 3 },
        ],
        'instanceGroups'
      );
    });
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(onSubmit).toHaveBeenCalledWith(mockDataForm, [3], [2]);
  });

  test('onSubmit does not get called if max_hosts value is out of range', async () => {
    const onSubmit = jest.fn();
    // mount with negative value
    let wrapper1;
    const mockDataNegative = JSON.parse(JSON.stringify(mockData));
    mockDataNegative.max_hosts = -5;
    await act(async () => {
      wrapper1 = mountWithContexts(
        <OrganizationForm
          organization={mockDataNegative}
          onSubmit={onSubmit}
          onCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });
    await waitForElement(wrapper1, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper1.find('button[aria-label="Save"]').simulate('click');
    });
    expect(onSubmit).not.toHaveBeenCalled();

    // mount with out of range value
    let wrapper2;
    const mockDataOutOfRange = JSON.parse(JSON.stringify(mockData));
    mockDataOutOfRange.max_hosts = 999999999999999999999;
    await act(async () => {
      wrapper2 = mountWithContexts(
        <OrganizationForm
          organization={mockDataOutOfRange}
          onSubmit={onSubmit}
          onCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });
    await waitForElement(wrapper2, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper2.find('button[aria-label="Save"]').simulate('click');
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  test('onSubmit is called and max_hosts value defaults to 0 if input is not a number', async () => {
    const onSubmit = jest.fn();
    // mount with String value (default to zero)
    const mockDataString = JSON.parse(JSON.stringify(mockData));
    mockDataString.max_hosts = 'Bee';
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockDataString}
          onSubmit={onSubmit}
          onCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(onSubmit).toHaveBeenCalledWith(
      {
        name: 'Foo',
        description: 'Bar',
        galaxy_credentials: [],
        max_hosts: 0,
        custom_virtualenv: 'Fizz',
      },
      [],
      []
    );
  });

  test('calls "onCancel" when Cancel button is clicked', async () => {
    const onCancel = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationForm
          organization={mockData}
          onSubmit={jest.fn()}
          onCancel={onCancel}
          me={meConfig.me}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(onCancel).toBeCalled();
  });
});
