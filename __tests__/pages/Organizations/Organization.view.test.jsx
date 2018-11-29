import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';
import { API_ORGANIZATIONS } from '../../../src/endpoints';
import OrganizationView from '../../../src/pages/Organizations/Organization.view';

describe('<OrganizationView />', () => {
  let pageWrapper;

  beforeEach(() => {
    pageWrapper = mount(
      <MemoryRouter initialEntries={['/organizations/1']}>
        <OrganizationView
          match={{ path: '/organizations/:id', route: 'organizations/1', link: 'organizations', params: { id: '1' } }}
          location={{ search: '', pathname: '' }}
        />
      </MemoryRouter>
    );
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
