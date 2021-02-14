import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Templates from './Templates';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

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
