import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ExecutionEnvironments from './ExecutionEnvironments';

describe('<ExecutionEnvironments/>', () => {
  let pageWrapper;
  let pageSections;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<ExecutionEnvironments />);
    pageSections = pageWrapper.find('PageSection');
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
    expect(pageSections.length).toBe(1);
    expect(pageSections.first().props().variant).toBe('light');
  });
});
