import React from 'react';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import Count from './Count';

describe('<Count />', () => {
  let pageWrapper;

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    pageWrapper = mountWithContexts(<Count link="foo" />);
    expect(pageWrapper.length).toBe(1);
  });

  test('renders non-failed version of count without prop', () => {
    pageWrapper = mountWithContexts(<Count link="foo" />);
    expect(pageWrapper.find('h2').hasClass('failed')).toBe(false);
  });

  test('renders failed version of count with appropriate prop', () => {
    pageWrapper = mountWithContexts(<Count link="foo" failed />);
    expect(pageWrapper.find('h2').hasClass('failed')).toBe(true);
  });
});
