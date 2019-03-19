import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import ExpandCollapse from '../../src/components/ExpandCollapse';

describe('<ExpandCollapse />', () => {
  const onCompact = jest.fn();
  const onExpand = jest.fn();
  const isCompact = false;
  test('initially renders without crashing', () => {
    const wrapper = mount(
      <I18nProvider>
        <ExpandCollapse
          onCompact={onCompact}
          onExpand={onExpand}
          isCompact={isCompact}
        />
      </I18nProvider>
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
});
