import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import InstanceGroups from './InstanceGroups';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<InstanceGroups/>', () => {
  let pageWrapper;
  let pageSections;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<InstanceGroups />);
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
