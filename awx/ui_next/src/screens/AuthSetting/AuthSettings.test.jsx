import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import AuthSettings from './AuthSettings';

describe('<AuthSettings />', () => {
  let pageWrapper;
  let pageSections;
  let title;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<AuthSettings />);
    pageSections = pageWrapper.find('PageSection');
    title = pageWrapper.find('Title');
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
    expect(pageSections.length).toBe(2);
    expect(title.length).toBe(1);
    expect(title.props().size).toBe('2xl');
    expect(pageSections.first().props().variant).toBe('light');
  });
});
