import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SmartInventoryButton from './SmartInventoryButton';

describe('<SmartInventoryButton />', () => {
  test('should render button', () => {
    const onClick = jest.fn();
    const wrapper = mountWithContexts(
      <SmartInventoryButton onClick={onClick} />
    );
    const button = wrapper.find('button');
    expect(button).toHaveLength(1);
    button.simulate('click');
    expect(onClick).toHaveBeenCalled();
  });
});
