import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import DraggableSelectedList from './DraggableSelectedList';

describe('<DraggableSelectedList />', () => {
  let wrapper;
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render expected rows', () => {
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
      {
        id: 2,
        name: 'bar',
      },
    ];
    wrapper = mountWithContexts(
      <DraggableSelectedList
        selected={mockSelected}
        onRemove={() => {}}
        onRowDrag={() => {}}
      />
    );
    expect(wrapper.find('DraggableSelectedList').length).toBe(1);
    expect(wrapper.find('DataListItem').length).toBe(2);
    expect(
      wrapper
        .find('DataListItem DataListCell')
        .first()
        .containsMatchingElement(<span>1. foo</span>)
    ).toEqual(true);
    expect(
      wrapper
        .find('DataListItem DataListCell')
        .last()
        .containsMatchingElement(<span>2. bar</span>)
    ).toEqual(true);
  });

  test('should not render when selected list is empty', () => {
    wrapper = mountWithContexts(
      <DraggableSelectedList
        selected={[]}
        onRemove={() => {}}
        onRowDrag={() => {}}
      />
    );
    expect(wrapper.find('DataList').length).toBe(0);
  });

  test('should call onRemove callback prop on remove button click', () => {
    const onRemove = jest.fn();
    const mockSelected = [
      {
        id: 1,
        name: 'foo',
      },
    ];
    wrapper = mountWithContexts(
      <DraggableSelectedList selected={mockSelected} onRemove={onRemove} />
    );
    wrapper
      .find('DataListItem[id="foo"] Button[aria-label="Remove"]')
      .simulate('click');
    expect(onRemove).toBeCalledWith({
      id: 1,
      name: 'foo',
    });
  });
});
