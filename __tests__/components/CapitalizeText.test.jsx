import React from 'react';
import { mount } from 'enzyme';
import CapitalizeText from '../../src/components/CapitalizeText';

describe('<CapitalizeText />', () => {
  let capitalizeTextWrapper;

  test('initially renders without crashing', () => {
    capitalizeTextWrapper = mount(
      <CapitalizeText text="foo" />
    );
    expect(capitalizeTextWrapper.length).toBe(1);
    expect(capitalizeTextWrapper.text()).toEqual('Foo');
    capitalizeTextWrapper.unmount();
  });
});
