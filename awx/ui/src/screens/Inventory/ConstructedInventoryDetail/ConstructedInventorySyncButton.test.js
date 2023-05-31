import React from 'react';
import { InventoriesAPI } from 'api';
import ConstructedInventorySyncButton from './ConstructedInventorySyncButton';
import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../../../api');

const inventory = { id: 100, name: 'Constructed Inventory' };

describe('<ConstructedInventorySyncButton />', () => {
  const Component = () => (
    <ConstructedInventorySyncButton inventoryId={inventory.id} />
  );

  test('should render start sync button', () => {
    render(<Component />);
    expect(
      screen.getByRole('button', { name: 'Start inventory source sync' })
    ).toBeInTheDocument();
  });

  test('should make expected api request on sync', async () => {
    render(<Component />);
    const syncButton = screen.queryByText('Sync');
    fireEvent.click(syncButton);
    await waitFor(() =>
      expect(InventoriesAPI.syncAllSources).toHaveBeenCalledWith(100)
    );
  });

  test('should show alert modal on throw', async () => {
    InventoriesAPI.syncAllSources.mockRejectedValueOnce(new Error());
    render(<Component />);
    await waitFor(() => {
      const syncButton = screen.queryByText('Sync');
      fireEvent.click(syncButton);
    });
    expect(screen.getByRole('dialog', { name: 'Alert modal Error!' }));
  });
});
