import React from 'react';
import { shallow } from 'enzyme';
import Credentials from './Credentials';

describe('<Credentials />', () => {
  test('should set breadcrumb config', () => {
    const wrapper = shallow(<Credentials />);

    const header = wrapper.find('ScreenHeader');
    expect(header.prop('streamType')).toEqual('credential');
    expect(header.prop('breadcrumbConfig')).toEqual({
      '/credentials': 'Credentials',
      '/credentials/add': 'Create New Credential',
    });
  });
});
