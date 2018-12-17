import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';

import { Nav } from '@patternfly/react-core';
import NavExpandableGroup from '../../src/components/NavExpandableGroup';

describe('NavExpandableGroup', () => {
  test('initialization and render', () => {
    const component = mount(
      <MemoryRouter initialEntries={['/foo']}>
        <Nav aria-label="Test Navigation">
          <NavExpandableGroup
            groupId="test"
            title="Test"
            routes={[
              { path: '/foo', title: 'Foo' },
              { path: '/bar', title: 'Bar' },
              { path: '/fiz', title: 'Fiz' },
            ]}
          />
        </Nav>
      </MemoryRouter>
    ).find('NavExpandableGroup').instance();

    expect(component.navItemPaths).toEqual(['/foo', '/bar', '/fiz']);
    expect(component.isActiveGroup()).toEqual(true);
  });
});
