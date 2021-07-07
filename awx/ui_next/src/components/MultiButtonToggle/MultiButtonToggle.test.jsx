import React from 'react';
import { shallow } from 'enzyme';
import MultiButtonToggle from './MultiButtonToggle';

describe('<MultiButtonToggle />', () => {
  let wrapper;
  const onChange = jest.fn();

  beforeAll(() => {
    wrapper = shallow(
      <MultiButtonToggle
        buttons={[
          ['yaml', 'YAML'],
          ['json', 'JSON'],
        ]}
        value="yaml"
        onChange={onChange}
        name="the-button"
      />
    );
  });

  it('should render buttons successfully', () => {
    const buttons = wrapper.find('SmallButton');
    expect(buttons.length).toBe(2);
    expect(buttons.at(0).props().variant).toBe('primary');
    expect(buttons.at(1).props().variant).toBe('secondary');
  });

  it('should call onChange function when button clicked', () => {
    const buttons = wrapper.find('SmallButton');
    buttons.at(1).simulate('click');
    expect(onChange).toHaveBeenCalledWith('json');
  });
});
