import React from 'react';
import { mount } from 'enzyme';
import Organizations from '../../src/pages/Organizations';

describe('<Organizations />', () => {
  let pageWrapper;
  let pageSections;
  let title;
  let gallery;
  let galleryItems;
  let orgCards;

  const orgs = [
    { id: 1, name: 'org 1' },
    { id: 2, name: 'org 2' },
    { id: 3, name: 'org 3' }
  ];

  const findOrgCards = () => {
    galleryItems = pageWrapper.find('GalleryItem');
    orgCards = pageWrapper.find('OrganizationCard');
  };

  beforeEach(() => {
    pageWrapper = mount(<Organizations />);
    pageSections = pageWrapper.find('PageSection');
    title = pageWrapper.find('Title');
    gallery = pageWrapper.find('Gallery');
    findOrgCards();
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
    expect(gallery.length).toBe(1);
    // by default, no galleryItems or orgCards
    expect(galleryItems.length).toBe(0);
    expect(orgCards.length).toBe(0);
    // will render all orgCards if state is set
    pageWrapper.setState({ organizations: orgs });
    findOrgCards();
    expect(galleryItems.length).toBe(3);
    expect(orgCards.length).toBe(3);
  });
});
