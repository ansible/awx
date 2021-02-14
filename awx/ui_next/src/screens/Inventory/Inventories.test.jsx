import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Inventories from './Inventories';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

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
