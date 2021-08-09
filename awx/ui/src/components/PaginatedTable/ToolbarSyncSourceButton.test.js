import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ToolbarSyncSourceButton from './ToolbarSyncSourceButton';

describe('<ToolbarSyncSourceButton />', () => {
  test('should render button', () => {
    const onClick = jest.fn();
    const wrapper = mountWithContexts(
      <ToolbarSyncSourceButton onClick={onClick} />
    );
    const button = wrapper.find('button');
    expect(button).toHaveLength(1);
    button.simulate('click');
    expect(onClick).toHaveBeenCalled();
  });
});
