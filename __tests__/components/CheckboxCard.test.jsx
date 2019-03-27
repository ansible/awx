import React from 'react';
import { mount } from 'enzyme';
import CheckboxCard from '../../src/components/AddRole/CheckboxCard';

describe('<CheckboxCard />', () => {
  let wrapper;
  test('initially renders without crashing', () => {
    wrapper = mount(
      <CheckboxCard
        name="Foobar"
        itemId={5}
      />
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
});
