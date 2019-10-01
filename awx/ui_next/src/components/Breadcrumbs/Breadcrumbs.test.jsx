import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import Breadcrumbs from './Breadcrumbs';

describe('<Breadcrumb />', () => {
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
    breadcrumb = breadcrumbWrapper.find('Breadcrumb');
    breadcrumbItem = breadcrumbWrapper.find('BreadcrumbItem');
    breadcrumbHeading = breadcrumbWrapper.find('BreadcrumbHeading');
  };

  test('initially renders succesfully', () => {
    breadcrumbWrapper = mount(
      <MemoryRouter initialEntries={['/foo/1/bar']} initialIndex={0}>
        <Breadcrumbs breadcrumbConfig={config} />
      </MemoryRouter>
    );

    findChildren();

    expect(breadcrumb).toHaveLength(1);
    expect(breadcrumbItem).toHaveLength(2);
    expect(breadcrumbHeading).toHaveLength(1);
    expect(breadcrumbItem.first().text()).toBe('Foo');
    expect(breadcrumbItem.last().text()).toBe('One');
    expect(breadcrumbHeading.text()).toBe('Bar');
    breadcrumbWrapper.unmount();
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
      breadcrumbWrapper = mount(
        <MemoryRouter initialEntries={[location]}>
          <Breadcrumbs breadcrumbConfig={config} />
        </MemoryRouter>
      );

      expect(breadcrumbWrapper.find('BreadcrumbItem')).toHaveLength(
        crumbLength
      );
      breadcrumbWrapper.unmount();
    });
  });
});
