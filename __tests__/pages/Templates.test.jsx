import React from 'react';
import { mountWithContexts } from '../enzymeHelpers';
import Templates from '../../src/pages/Templates';

describe('<Templates />', () => {
  let pageWrapper;
  let pageSections;
  let title;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<Templates />);
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
