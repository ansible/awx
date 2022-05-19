import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { Router, Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import PersistentFilters from './PersistentFilters';

const KEY = 'awx-persistent-filter';

describe('PersistentFilters', () => {
  test('should initialize filter in sessionStorage', () => {
    expect(sessionStorage.getItem(KEY)).toEqual(null);
    const history = createMemoryHistory({
      initialEntries: ['/templates'],
    });
    render(
      <Router history={history}>
        <PersistentFilters pageKey="templates">test</PersistentFilters>
      </Router>
    );

    expect(JSON.parse(sessionStorage.getItem(KEY))).toEqual({
      pageKey: 'templates',
      qs: '',
    });
  });

  test('should restore filters from sessionStorage', () => {
    expect(
      sessionStorage.setItem(
        KEY,
        JSON.stringify({
          pageKey: 'templates',
          qs: '?page=2&name=foo',
        })
      )
    );
    const history = createMemoryHistory({
      initialEntries: ['/templates?restoreFilters=true'],
    });
    render(
      <Router history={history}>
        <PersistentFilters pageKey="templates">test</PersistentFilters>
      </Router>
    );

    expect(history.location.search).toEqual('?page=2&name=foo');
  });

  test('should not restore filters without restoreFilters query param', () => {
    expect(
      sessionStorage.setItem(
        KEY,
        JSON.stringify({
          pageKey: 'templates',
          qs: '?page=2&name=foo',
        })
      )
    );
    const history = createMemoryHistory({
      initialEntries: ['/templates'],
    });
    render(
      <Router history={history}>
        <PersistentFilters pageKey="templates">test</PersistentFilters>
      </Router>
    );

    expect(history.location.search).toEqual('');
  });

  test("should not restore filters if page key doesn't match", () => {
    expect(
      sessionStorage.setItem(
        KEY,
        JSON.stringify({
          pageKey: 'projects',
          qs: '?page=2&name=foo',
        })
      )
    );
    const history = createMemoryHistory({
      initialEntries: ['/templates?restoreFilters=true'],
    });
    render(
      <Router history={history}>
        <PersistentFilters pageKey="templates">test</PersistentFilters>
      </Router>
    );

    expect(history.location.search).toEqual('');
  });

  test('should update stored filters when qs changes', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates'],
    });
    render(
      <Router history={history}>
        <PersistentFilters pageKey="templates">test</PersistentFilters>
      </Router>
    );

    history.push('/templates?page=3');
    await waitFor(() => true);

    expect(JSON.parse(sessionStorage.getItem(KEY))).toEqual({
      pageKey: 'templates',
      qs: '?page=3',
    });
  });
});
