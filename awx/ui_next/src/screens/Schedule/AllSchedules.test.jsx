import React from 'react';
import { shallow } from 'enzyme';
import AllSchedules from './AllSchedules';

describe('<AllSchedules />', () => {
  test('should set breadcrumb config', () => {
    const wrapper = shallow(<AllSchedules />);

    const header = wrapper.find('ScreenHeader');
    expect(header.prop('streamType')).toEqual('schedule');
    expect(header.prop('breadcrumbConfig')).toEqual({
      '/schedules': 'Schedules',
    });
  });
});
