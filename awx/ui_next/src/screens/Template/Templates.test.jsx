import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Templates from './Templates';

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
