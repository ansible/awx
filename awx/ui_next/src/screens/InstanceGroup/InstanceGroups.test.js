import React from 'react';
import { shallow } from 'enzyme';

import InstanceGroups from './InstanceGroups';

describe('<InstanceGroups/>', () => {
  test('should set breadcrumbs', () => {
    const wrapper = shallow(<InstanceGroups />);

    const header = wrapper.find('ScreenHeader');
    expect(header.prop('streamType')).toEqual('instance_group');
    expect(header.prop('breadcrumbConfig')).toEqual({
      '/instance_groups': 'Instance Groups',
      '/instance_groups/add': 'Create new instance group',
      '/instance_groups/container_group/add': 'Create new container group',
    });
  });
});
