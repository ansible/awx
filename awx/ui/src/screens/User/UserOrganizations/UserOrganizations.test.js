import React from 'react';
import { shallow } from 'enzyme';

import UserOrganizations from './UserOrganizations';

describe('<UserOrganizations />', () => {
  test('should render UserOrganizationList', () => {
    const wrapper = shallow(<UserOrganizations />);
    expect(wrapper.find('UserOrganizationList')).toHaveLength(1);
  });
});
