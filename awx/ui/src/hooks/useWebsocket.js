import { useState, useEffect, useRef } from 'react';

export default function useWebsocket(subscribeGroups) {
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(
      `${window.location.protocol === 'http:' ? 'ws:' : 'wss:'}//${
        window.location.host
      }${window.location.pathname}websocket/`
    );

    const connect = () => {
      const xrftoken = `; ${document.cookie}`
        .split('; csrftoken=')
        .pop()
        .split(';')
        .shift();
      ws.current.send(
        JSON.stringify({
          xrftoken,
          groups: subscribeGroups,
        })
      );
    };
    ws.current.onopen = connect;

    ws.current.onmessage = (e) => {
      setLastMessage(JSON.parse(e.data));
    };

    ws.current.onclose = (e) => {
      if (e.code !== 1000) {
        // eslint-disable-next-line no-console
        console.debug('Socket closed. Reconnecting...', e);
        setTimeout(() => {
          connect();
        }, 1000);
      }
    };

    ws.current.onerror = (err) => {
      // eslint-disable-next-line no-console
      console.debug('Socket error: ', err, 'Disconnecting...');
      ws.current.close();
    };

    return () => {
      ws.current.close();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return lastMessage;
}
