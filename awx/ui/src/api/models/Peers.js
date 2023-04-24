import Base from '../Base';

class Peers extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/peers/';

    this.createPeer = this.createPeer.bind(this);
    this.destroyPeer = this.destroyPeer.bind(this);
  }

  createPeer(sourceId, targetId) {
    return this.http.post(`${this.baseUrl}`, {
      source: sourceId,
      target: targetId,
      link_state: 'established'
    });
  }

  destroyPeer(sourceId, targetId) {

    const { data } = this.read({
      page: 1,
      page_size: 200,
      source: sourceId,
      target: targetId,
    });

    const [peer_delete] = Promise.all(
      data.results
        .map((peer) =>
          this.destroy(peer.id)
        )
    );

    return peer_delete
  }

}

export default Peers;
