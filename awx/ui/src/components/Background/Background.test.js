import React from 'react';
import { mount } from 'enzyme';

import Background from './Background';

describe('Background', () => {
  test('renders the expected content', () => {
    const wrapper = mount(
      <Background>
        <div id="test" />
      </Background>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('.pf-c-background-image')).toHaveLength(1);
    expect(wrapper.find('#test')).toHaveLength(1);
  });
});
