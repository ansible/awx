import { useState, useEffect } from 'react';
import useWebsocket from '../../../util/useWebsocket';
import useThrottle from '../../../util/useThrottle';

export default function useWsProjects(
  initialInventories,
  fetchInventoriesById
) {
  const [inventories, setInventories] = useState(initialInventories);
  const [inventoriesToFetch, setInventoriesToFetch] = useState([]);
  const throttledInventoriesToFetch = useThrottle(inventoriesToFetch, 5000);
  const lastMessage = useWebsocket({
    inventories: ['status_changed'],
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setInventories(initialInventories);
  }, [initialInventories]);

  const enqueueId = id => {
    if (!inventoriesToFetch.includes(id)) {
      setInventoriesToFetch(ids => ids.concat(id));
    }
  };
  useEffect(
    function fetchUpdatedInventories() {
      (async () => {
        if (!throttledInventoriesToFetch.length) {
          return;
        }
        setInventoriesToFetch([]);
        const newInventories = await fetchInventoriesById(
          throttledInventoriesToFetch
        );
        let updated = inventories;
        newInventories.forEach(inventory => {
          const index = inventories.findIndex(i => i.id === inventory.id);
          if (index === -1) {
            return;
          }
          updated = [
            ...updated.slice(0, index),
            inventory,
            ...updated.slice(index + 1),
          ];
        });
        setInventories(updated);
      })();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [throttledInventoriesToFetch, fetchInventoriesById]
  );

  useEffect(
    function processWsMessage() {
      if (
        !lastMessage?.inventory_id ||
        lastMessage.type !== 'inventory_update'
      ) {
        return;
      }
      const index = inventories.findIndex(
        p => p.id === lastMessage.inventory_id
      );
      if (index === -1) {
        return;
      }

      if (!['pending', 'waiting', 'running'].includes(lastMessage.status)) {
        enqueueId(lastMessage.inventory_id);
        return;
      }

      const inventory = inventories[index];
      const updatedInventory = {
        ...inventory,
        isSourceSyncRunning: true,
      };
      setInventories([
        ...inventories.slice(0, index),
        updatedInventory,
        ...inventories.slice(index + 1),
      ]);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps,
    [lastMessage]
  );

  return inventories;
}
