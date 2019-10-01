import React from 'react';
import { mount } from 'enzyme';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Sparkline from './Sparkline';

describe('Sparkline', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<Sparkline />);
    expect(wrapper).toHaveLength(1);
  });
  test('renders an icon with tooltips and links for each job', () => {
    const jobs = [
      {
        id: 1,
        status: 'successful',
        finished: '2019-08-08T15:27:57.320120Z',
      },
      {
        id: 2,
        status: 'failed',
        finished: '2019-08-09T15:27:57.320120Z',
      },
    ];
    const wrapper = mountWithContexts(<Sparkline jobs={jobs} />);
    expect(wrapper.find('StatusIcon')).toHaveLength(2);
    expect(wrapper.find('Tooltip')).toHaveLength(2);
    expect(wrapper.find('Link')).toHaveLength(2);
  });
});
