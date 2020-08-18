import { useState, useEffect } from 'react';
import useWebsocket from '../../../util/useWebsocket';

export default function useWsWorkflowOutput(workflowJobId, initialNodes) {
  const [nodes, setNodes] = useState(initialNodes);
  const lastMessage = useWebsocket({
    jobs: ['status_changed'],
    control: ['limit_reached_1'],
  });

  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes]);

  useEffect(
    function parseWsMessage() {
      if (
        !nodes ||
        nodes.length === 0 ||
        lastMessage?.workflow_job_id !== workflowJobId
      ) {
        return;
      }

      const index = nodes.findIndex(
        node => node?.originalNodeObject?.id === lastMessage.workflow_node_id
      );

      if (index > -1) {
        setNodes(updateNode(nodes, index, lastMessage));
      }
    },
    [lastMessage] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return nodes;
}

function updateNode(nodes, index, message) {
  const node = {
    ...nodes[index],
    originalNodeObject: {
      ...nodes[index]?.originalNodeObject,
      job: message.unified_job_id,
      summary_fields: {
        ...nodes[index]?.originalNodeObject?.summary_fields,
        job: {
          ...nodes[index]?.originalNodeObject?.summary_fields?.job,
          id: message.unified_job_id,
          status: message.status,
          type: message.type,
        },
      },
    },
    job: {
      ...nodes[index]?.job,
      id: message.unified_job_id,
      name: nodes[index]?.job?.name || nodes[index]?.unifiedJobTemplate?.name,
      status: message.status,
      type: message.type,
    },
  };

  return [...nodes.slice(0, index), node, ...nodes.slice(index + 1)];
}
