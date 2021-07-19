import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ToolbarAddButton from './ToolbarAddButton';

describe('<ToolbarAddButton />', () => {
  test('should render button', () => {
    const onClick = jest.fn();
    const wrapper = mountWithContexts(<ToolbarAddButton onClick={onClick} />);
    const button = wrapper.find('button');
    expect(button).toHaveLength(1);
    button.simulate('click');
    expect(onClick).toHaveBeenCalled();
  });

  test('should render link', () => {
    const wrapper = mountWithContexts(<ToolbarAddButton linkTo="/foo" />);
    const link = wrapper.find('Link');
    expect(link).toHaveLength(1);
    expect(link.prop('to')).toBe('/foo');
  });

  test('should render link with toggle icon', () => {
    const wrapper = mountWithContexts(
      <ToolbarAddButton showToggleIndicator linkTo="/foo" />
    );
    const link = wrapper.find('Link');
    expect(link).toHaveLength(1);
    expect(link.prop('to')).toBe('/foo');
  });
});
