import React from 'react';
import { MemoryRouter } from 'react-router-dom';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ScreenHeader from './ScreenHeader';

describe('<ScreenHeader />', () => {
  let breadcrumbWrapper;
  let breadcrumb;
  let breadcrumbItem;
  let breadcrumbHeading;

  const config = {
    '/foo': 'Foo',
    '/foo/1': 'One',
    '/foo/1/bar': 'Bar',
    '/foo/1/bar/fiz': 'Fiz',
  };

  const findChildren = () => {
    breadcrumb = breadcrumbWrapper.find('ScreenHeader');
    breadcrumbItem = breadcrumbWrapper.find('BreadcrumbItem');
    breadcrumbHeading = breadcrumbWrapper.find('Title');
  };

  test('initially renders successfully', () => {
    breadcrumbWrapper = mountWithContexts(
      <MemoryRouter initialEntries={['/foo/1/bar']} initialIndex={0}>
        <ScreenHeader streamType="all_activity" breadcrumbConfig={config} />
      </MemoryRouter>
    );

    findChildren();

    expect(breadcrumb).toHaveLength(1);
    expect(breadcrumbItem).toHaveLength(2);
    expect(breadcrumbHeading).toHaveLength(1);
    expect(breadcrumbItem.first().text()).toBe('Foo');
    expect(breadcrumbItem.last().text()).toBe('One');
    expect(breadcrumbHeading.text()).toBe('Bar');
  });

  test('renders breadcrumb items defined in breadcrumbConfig', () => {
    const routes = [
      ['/fo', 0],
      ['/foo', 0],
      ['/foo/1', 1],
      ['/foo/baz', 1],
      ['/foo/1/bar', 2],
      ['/foo/1/bar/fiz', 3],
    ];

    routes.forEach(([location, crumbLength]) => {
      breadcrumbWrapper = mountWithContexts(
        <MemoryRouter initialEntries={[location]}>
          <ScreenHeader streamType="all_activity" breadcrumbConfig={config} />
        </MemoryRouter>
      );

      expect(breadcrumbWrapper.find('BreadcrumbItem')).toHaveLength(
        crumbLength
      );
    });
  });
});
