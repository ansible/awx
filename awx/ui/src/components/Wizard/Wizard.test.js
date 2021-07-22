import React from 'react';
import { mount } from 'enzyme';
import Wizard from './Wizard';

describe('Wizard', () => {
  test('renders the expected content', () => {
    const wrapper = mount(
      <Wizard
        title="Simple Wizard"
        steps={[{ name: 'Step 1', component: <p>Step 1</p> }]}
      />
    );
    expect(wrapper).toHaveLength(1);
  });
});
