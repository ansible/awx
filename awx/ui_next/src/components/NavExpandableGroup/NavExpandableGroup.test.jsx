import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';

import { Nav } from '@patternfly/react-core';
import NavExpandableGroup from './NavExpandableGroup';

describe('NavExpandableGroup', () => {
  test('initialization and render', () => {
    const component = mount(
      <MemoryRouter initialEntries={['/foo']}>
        <Nav aria-label="Test Navigation">
          <NavExpandableGroup
            groupId="test"
            groupTitle="Test"
            routes={[
              { path: '/foo', title: 'Foo' },
              { path: '/bar', title: 'Bar' },
              { path: '/fiz', title: 'Fiz' },
            ]}
          />
        </Nav>
      </MemoryRouter>
    )
      .find('NavExpandableGroup')
      .instance();

    expect(component.navItemPaths).toEqual(['/foo', '/bar', '/fiz']);
    expect(component.isActiveGroup()).toEqual(true);
  });

  describe('isActivePath', () => {
    const params = [
      ['/fo', '/foo', false],
      ['/foo', '/foo', true],
      ['/foo/1/bar/fiz', '/foo', true],
      ['/foo/1/bar/fiz', 'foo', false],
      ['/foo/1/bar/fiz', 'foo/', false],
      ['/foo/1/bar/fiz', '/bar', false],
      ['/foo/1/bar/fiz', '/fiz', false],
    ];

    params.forEach(([location, path, expected]) => {
      test(`when location is ${location}, isActivePath('${path}') returns ${expected} `, () => {
        const component = mount(
          <MemoryRouter initialEntries={[location]}>
            <Nav aria-label="Test Navigation">
              <NavExpandableGroup
                groupId="test"
                groupTitle="Test"
                routes={[
                  { path: '/foo', title: 'Foo' },
                  { path: '/bar', title: 'Bar' },
                  { path: '/fiz', title: 'Fiz' },
                ]}
              />
            </Nav>
          </MemoryRouter>
        )
          .find('NavExpandableGroup')
          .instance();

        expect(component.isActivePath(path)).toEqual(expected);
      });
    });
  });
});
