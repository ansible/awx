import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import FilterTags from './FilterTags';

describe('<ExpandCollapse />', () => {
  const qsConfig = {
    namespace: 'item',
    defaultParams: { page: 1, page_size: 5, order_by: 'name' },
    integerFields: [],
  };
  const onRemoveFn = jest.fn();
  const onRemoveAllFn = jest.fn();

  test('initially renders without crashing', () => {
    const wrapper = mountWithContexts(
      <FilterTags
        qsConfig={qsConfig}
        onRemove={onRemoveFn}
        onRemoveAll={onRemoveAllFn}
      />
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });

  test('renders non-default param tags based on location history', () => {
    const history = createMemoryHistory({
      initialEntries: [
        '/foo?item.page=1&item.page_size=2&item.name__icontains=bar&item.job_type__icontains=project',
      ],
    });
    const wrapper = mountWithContexts(
      <FilterTags
        qsConfig={qsConfig}
        onRemove={onRemoveFn}
        onRemoveAll={onRemoveAllFn}
      />,
      {
        context: { router: { history, route: { location: history.location } } },
      }
    );
    const chips = wrapper.find('.pf-c-chip.searchTagChip');
    expect(chips.length).toBe(2);
    const chipLabels = wrapper.find('.pf-c-chip__text b');
    expect(chipLabels.length).toBe(2);
    expect(chipLabels.at(0).text()).toEqual('Name:');
    expect(chipLabels.at(1).text()).toEqual('Job Type:');
    wrapper.unmount();
  });
});
