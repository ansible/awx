import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import HeaderRow, { HeaderCell } from './HeaderRow';

describe('<HeaderRow />', () => {
  const qsConfig = {
    defaultParams: {
      order_by: 'one',
    },
  };

  test('should render cells', async () => {
    const wrapper = mountWithContexts(
      <table>
        <HeaderRow qsConfig={qsConfig}>
          <HeaderCell sortKey="one">One</HeaderCell>
          <HeaderCell>Two</HeaderCell>
        </HeaderRow>
      </table>
    );

    const cells = wrapper.find('Th');
    expect(cells).toHaveLength(3);
    expect(cells.at(1).text()).toEqual('One');
    expect(cells.at(2).text()).toEqual('Two');
  });

  test('should provide sort controls', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/list'],
    });
    const wrapper = mountWithContexts(
      <table>
        <HeaderRow qsConfig={qsConfig}>
          <HeaderCell sortKey="one">One</HeaderCell>
          <HeaderCell>Two</HeaderCell>
        </HeaderRow>
      </table>,
      { context: { router: { history } } }
    );

    const cell = wrapper.find('Th').at(1);
    cell.prop('sort').onSort({}, '', 'desc');
    expect(history.location.search).toEqual('?order_by=-one');
  });

  test('should not sort cells without a sortKey', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/list'],
    });
    const wrapper = mountWithContexts(
      <table>
        <HeaderRow qsConfig={qsConfig}>
          <HeaderCell sortKey="one">One</HeaderCell>
          <HeaderCell>Two</HeaderCell>
        </HeaderRow>
      </table>,
      { context: { router: { history } } }
    );

    const cell = wrapper.find('Th').at(2);
    expect(cell.prop('sort')).toEqual(null);
  });
});
