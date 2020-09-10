import { useState, useEffect } from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import {
  parseQueryString,
  replaceParams,
  encodeNonDefaultQueryString,
} from '../../../util/qs';
import useWebsocket from '../../../util/useWebsocket';
import useThrottle from '../../../util/useThrottle';

export default function useWsInventories(
  initialInventories,
  fetchInventories,
  fetchInventoriesById,
  qsConfig
) {
  const location = useLocation();
  const history = useHistory();
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
        const updated = [...inventories];
        newInventories.forEach(inventory => {
          const index = inventories.findIndex(i => i.id === inventory.id);
          if (index === -1) {
            return;
          }
          updated[index] = inventory;
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
        (lastMessage.type !== 'inventory_update' &&
          lastMessage.group_name !== 'inventories')
      ) {
        return;
      }
      const index = inventories.findIndex(
        p => p.id === lastMessage.inventory_id
      );
      if (index === -1) {
        return;
      }

      const params = parseQueryString(qsConfig, location.search);

      const inventory = inventories[index];
      const updatedInventory = {
        ...inventory,
      };

      if (
        lastMessage.group_name === 'inventories' &&
        lastMessage.status === 'deleted' &&
        inventories.length === 1 &&
        params.page > 1
      ) {
        // We've deleted the last inventory on this page so we'll
        // try to navigate back to the previous page
        const newParams = encodeNonDefaultQueryString(
          qsConfig,
          replaceParams(params, {
            page: params.page - 1,
          })
        );
        history.push(`${location.pathname}?${newParams}`);
        return;
      }

      if (
        lastMessage.group_name === 'inventories' &&
        lastMessage.status === 'deleted'
      ) {
        fetchInventories();
        return;
      }

      if (
        !['pending', 'waiting', 'running', 'pending_deletion'].includes(
          lastMessage.status
        )
      ) {
        enqueueId(lastMessage.inventory_id);
        return;
      }

      if (
        lastMessage.group_name === 'inventories' &&
        lastMessage.status === 'pending_deletion'
      ) {
        updatedInventory.pending_deletion = true;
      }

      if (lastMessage.group_name !== 'inventories') {
        updatedInventory.isSourceSyncRunning = true;
      }

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
