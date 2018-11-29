import React from 'react';
import { mount } from 'enzyme';
import { API_ORGANIZATIONS } from '../../../src/endpoints';
import OrganizationAdd from '../../../src/pages/Organizations/Organization.add';

describe('<OrganizationAdd />', () => {
  let pageWrapper;

  beforeEach(() => {
    pageWrapper = mount(<OrganizationAdd />);
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
  });

  test('API Organization endpoint is valid', () => {
    expect(API_ORGANIZATIONS).toBeDefined();
  });
});
