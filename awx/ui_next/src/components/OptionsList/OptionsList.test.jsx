import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { getQSConfig } from '../../util/qs';
import OptionsList from './OptionsList';

const qsConfig = getQSConfig('test', { order_by: 'foo' });

describe('<OptionsList />', () => {
  it('should display list of options', () => {
    const options = [
      { id: 1, name: 'foo', url: '/item/1' },
      { id: 2, name: 'bar', url: '/item/2' },
      { id: 3, name: 'baz', url: '/item/3' },
    ];
    const wrapper = mountWithContexts(
      <OptionsList
        value={[]}
        options={options}
        optionCount={3}
        searchColumns={[
          { name: 'Foo', key: 'foo__icontains', isDefault: true },
        ]}
        sortColumns={[{ name: 'Foo', key: 'foo' }]}
        qsConfig={qsConfig}
        selectItem={() => {}}
        deselectItem={() => {}}
        name="Item"
      />
    );
    expect(wrapper.find('PaginatedDataList').prop('items')).toEqual(options);
    expect(wrapper.find('SelectedList')).toHaveLength(0);
  });

  it('should render selected list', () => {
    const options = [
      { id: 1, name: 'foo', url: '/item/1' },
      { id: 2, name: 'bar', url: '/item/2' },
      { id: 3, name: 'baz', url: '/item/3' },
    ];
    const wrapper = mountWithContexts(
      <OptionsList
        value={[options[1]]}
        options={options}
        optionCount={3}
        searchColumns={[
          { name: 'Foo', key: 'foo__icontains', isDefault: true },
        ]}
        sortColumns={[{ name: 'Foo', key: 'foo' }]}
        qsConfig={qsConfig}
        selectItem={() => {}}
        deselectItem={() => {}}
        name="Item"
      />
    );
    const list = wrapper.find('SelectedList');
    expect(list).toHaveLength(1);
    expect(list.prop('selected')).toEqual([options[1]]);
  });
});
