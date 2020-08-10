import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import NotificationTemplates from './NotificationTemplates';

describe('<NotificationTemplates />', () => {
  let pageWrapper;
  let pageSections;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<NotificationTemplates />);
    pageSections = pageWrapper.find('PageSection');
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
    expect(pageSections.length).toBe(2);
    expect(pageSections.first().props().variant).toBe('light');
  });
});
