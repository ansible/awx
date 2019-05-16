import React from 'react';
import { mountWithContexts } from '../enzymeHelpers';
import Schedules from '../../src/pages/Schedules';

describe('<Schedules />', () => {
  let pageWrapper;
  let pageSections;
  let title;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<Schedules />);
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
    pageSections.forEach(section => {
      expect(section.props().variant).toBeDefined();
    });
  });
});
