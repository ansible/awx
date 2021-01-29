import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ActivityStream from './ActivityStream';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<ActivityStream />', () => {
  let pageWrapper;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<ActivityStream />);
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
  });
});
