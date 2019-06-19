import React from 'react';
import Templates from './Templates';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

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
