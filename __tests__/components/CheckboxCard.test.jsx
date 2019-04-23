import React from 'react';
import { shallow } from 'enzyme';
import CheckboxCard from '../../src/components/AddRole/CheckboxCard';

describe('<CheckboxCard />', () => {
  let wrapper;
  test('initially renders without crashing', () => {
    wrapper = shallow(
      <CheckboxCard
        name="Foobar"
        itemId={5}
      />
    );
    expect(wrapper.length).toBe(1);
  });
});
