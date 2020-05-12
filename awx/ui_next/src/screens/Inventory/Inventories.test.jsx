import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Inventories from './Inventories';

describe('<Inventories />', () => {
  let pageWrapper;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<Inventories />);
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
  });
});
