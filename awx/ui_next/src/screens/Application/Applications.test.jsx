import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Applications from './Applications';

describe('<Applications />', () => {
  let pageWrapper;
  let pageSections;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<Applications />);
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
