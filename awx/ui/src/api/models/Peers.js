import Base from '../Base';

class Peers extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/peers/';
  }

  addPeer(sourceId, targetId) {
    return this.http.post(`${this.baseUrl}`, {
      source: sourceId, 
      target: targetId,
      link_state: 'established'
    });
  }

  deletePeer(sourceId, targetId) {

    const { data } = await this.read({
      page: 1,
      page_size: 200,
      source: sourceId,
      target: targetId,
    });

    const [peer_delete] = await Promise.all(
      data.results
        .map((peer) =>
          this.destroy(peer.id)
        )
    );

    return peer_delete
  }

}

export default Peers;
