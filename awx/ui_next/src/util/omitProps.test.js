import React from 'react';
import { mount } from 'enzyme';
import omitProps from './omitProps';

describe('omitProps', () => {
  test('should render child component', () => {
    const Omit = omitProps('div');
    const wrapper = mount(<Omit foo="one" bar="two" />);

    const div = wrapper.find('div');
    expect(div).toHaveLength(1);
    expect(div.prop('foo')).toEqual('one');
    expect(div.prop('bar')).toEqual('two');
  });

  test('should not pass omitted props to child component', () => {
    const Omit = omitProps('div', 'foo', 'bar');
    const wrapper = mount(<Omit foo="one" bar="two" />);

    const div = wrapper.find('div');
    expect(div).toHaveLength(1);
    expect(div.prop('foo')).toEqual(undefined);
    expect(div.prop('bar')).toEqual(undefined);
  });

  test('should support mix of omitted and non-omitted props', () => {
    const Omit = omitProps('div', 'foo');
    const wrapper = mount(<Omit foo="one" bar="two" />);

    const div = wrapper.find('div');
    expect(div).toHaveLength(1);
    expect(div.prop('foo')).toEqual(undefined);
    expect(div.prop('bar')).toEqual('two');
  });
});
