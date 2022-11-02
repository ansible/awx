import React from 'react';
import { shallow } from 'enzyme';
import { InstanceGroupsAPI } from 'api';
import InstanceGroups from './InstanceGroups';
import { useUserProfile } from 'contexts/Config';

const mockUseLocationValue = {
  pathname: '',
};
jest.mock('api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => mockUseLocationValue,
}));

beforeEach(() => {
  useUserProfile.mockImplementation(() => {
    return {
      isSuperUser: true,
      isSystemAuditor: false,
      isOrgAdmin: false,
      isNotificationAdmin: false,
      isExecEnvAdmin: false,
    };
  });
});

describe('<InstanceGroups/>', () => {
  test('should set breadcrumbs', () => {
    mockUseLocationValue.pathname = '/instance_groups';

    const wrapper = shallow(<InstanceGroups />);

    const header = wrapper.find('ScreenHeader');
    expect(header.prop('streamType')).toEqual('instance_group');
    expect(header.prop('breadcrumbConfig')).toEqual({
      '/instance_groups': 'Instance Groups',
      '/instance_groups/add': 'Create new instance group',
      '/instance_groups/container_group/add': 'Create new container group',
    });
  });
  test('should set breadcrumbs', async () => {
    mockUseLocationValue.pathname = '/instance_groups/1/instances';
    InstanceGroupsAPI.readInstances.mockResolvedValue({
      data: { results: [{ hostname: 'EC2', id: 1 }] },
    });
    InstanceGroupsAPI.readInstanceOptions.mockResolvedValue({
      data: { actions: {} },
    });

    const wrapper = shallow(<InstanceGroups />);

    expect(wrapper.find('ScreenHeader').prop('streamType')).toEqual('instance');
  });
});
