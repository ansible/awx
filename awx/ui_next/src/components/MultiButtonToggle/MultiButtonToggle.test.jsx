import React from 'react';
import { mount } from 'enzyme';
import MultiButtonToggle from './MultiButtonToggle';

describe('<MultiButtonToggle />', () => {
  let wrapper;
  const onChange = jest.fn();
  beforeAll(() => {
    wrapper = mount(
      <MultiButtonToggle
        buttons={[
          ['yaml', 'YAML'],
          ['json', 'JSON'],
        ]}
        value="yaml"
        onChange={onChange}
      />
    );
  });
  afterAll(() => {
    wrapper.unmount();
  });
  it('should render buttons successfully', () => {
    const buttons = wrapper.find('Button');
    expect(buttons.length).toBe(2);
    expect(buttons.at(0).props().variant).toBe('primary');
    expect(buttons.at(1).props().variant).toBe('secondary');
  });
  it('should call onChange function when button clicked', () => {
    const buttons = wrapper.find('Button');
    buttons.at(1).simulate('click');
    expect(onChange).toHaveBeenCalledWith('json');
  });
});
