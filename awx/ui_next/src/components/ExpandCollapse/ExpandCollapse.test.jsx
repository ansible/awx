import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ExpandCollapse from './ExpandCollapse';

describe('<ExpandCollapse />', () => {
  const onCompact = jest.fn();
  const onExpand = jest.fn();
  const isCompact = false;
  test('initially renders without crashing', () => {
    const wrapper = mountWithContexts(
      <ExpandCollapse
        onCompact={onCompact}
        onExpand={onExpand}
        isCompact={isCompact}
      />
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
});
