import React from 'react';
import { mount } from 'enzyme';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Sparkline from './Sparkline';

describe('Sparkline', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<Sparkline />);
    expect(wrapper).toHaveLength(1);
  });
  test('renders an icon for each job', () => {
    const jobs = [
      {
        id: 1,
        status: 'successful'
      }, {
        id: 2,
        status: 'failed'
      }
    ]
    const wrapper = mountWithContexts(<Sparkline jobs={jobs} />);
    expect(wrapper.find('JobStatusIcon')).toHaveLength(2);
  });
});
