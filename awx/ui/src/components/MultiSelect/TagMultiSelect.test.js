import React from 'react';
import { mount } from 'enzyme';
import TagMultiSelect from './TagMultiSelect';

describe('<TagMultiSelect />', () => {
  it('should render Select', () => {
    const wrapper = mount(
      <TagMultiSelect value="foo,bar" onChange={jest.fn()} />
    );
    wrapper.find('input').simulate('focus');
    const options = wrapper.find('Chip');
    expect(options).toHaveLength(2);
    expect(options.at(0).text()).toEqual('foo');
    expect(options.at(1).text()).toEqual('bar');
  });

  it('should not treat empty string as an option', () => {
    const wrapper = mount(<TagMultiSelect value="" onChange={jest.fn()} />);
    wrapper.find('SelectToggle').simulate('click');
    expect(wrapper.find('Select').prop('isOpen')).toEqual(true);
    expect(wrapper.find('Chip')).toHaveLength(0);
  });

  it('should trigger onChange', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <TagMultiSelect value="foo,bar" onChange={onChange} />
    );
    wrapper.find('input').simulate('focus');

    wrapper.find('Select').invoke('onSelect')(null, 'baz');
    expect(onChange).toHaveBeenCalledWith('foo,bar,baz');
  });
});
