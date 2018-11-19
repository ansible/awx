import React from 'react';
import { HashRouter } from 'react-router-dom';

import { mount } from 'enzyme';

import api from '../../src/api';
import { API_ORGANIZATIONS } from '../../src/endpoints';
import Organizations from '../../src/pages/Organizations';

describe('<Organizations />', () => {
  let pageWrapper;

  const results = [
    {
      id: 1,
      name: 'org 1',
      summary_fields: {
        related_field_counts: {
          users: 1,
          teams: 1,
          admins: 1
        }
      }
    },
    {
      id: 2,
      name: 'org 2',
      summary_fields: {
        related_field_counts: {
          users: 1,
          teams: 1,
          admins: 1
        }
      }
    },
    {
      id: 3,
      name: 'org 3',
      summary_fields: {
        related_field_counts: {
          users: 1,
          teams: 1,
          admins: 1
        }
      }
    },
  ];
  const count = results.length;
  const response = { data: { count, results } };

  beforeEach(() => {
    api.get = jest.fn().mockImplementation(() => Promise.resolve(response));
    pageWrapper = mount(<HashRouter><Organizations /></HashRouter>);
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('it renders expected content', () => {
    const pageSections = pageWrapper.find('PageSection');
    const title = pageWrapper.find('Title');

    expect(pageWrapper.length).toBe(1);
    expect(pageSections.length).toBe(2);
    expect(title.length).toBe(1);
    expect(title.props().size).toBe('2xl');
    pageSections.forEach(section => {
      expect(section.props().variant).toBeDefined();
    });
    expect(pageWrapper.find('ul').length).toBe(1);
    expect(pageWrapper.find('ul li').length).toBe(0);
    // will render all list items on update
    pageWrapper.update();
    expect(pageWrapper.find('ul li').length).toBe(count);
  });

  test('API Organization endpoint is valid', () => {
    expect(API_ORGANIZATIONS).toBeDefined();
  });

  test('it displays a tooltip on delete hover', () => {
    const tooltip = '.pf-c-tooltip__content';
    const deleteButton = 'button[aria-label="Delete"]';

    expect(pageWrapper.find(tooltip).length).toBe(0);
    pageWrapper.find(deleteButton).simulate('mouseover');
    expect(pageWrapper.find(tooltip).length).toBe(1);
  });
});
