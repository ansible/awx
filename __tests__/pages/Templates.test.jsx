import React from 'react';
import Templates from '../../src/pages/Templates/Templates';
import { mountWithContexts } from '../enzymeHelpers';

describe('<Templates />', () => {
  let pageWrapper;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<Templates />);
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
  });
});
