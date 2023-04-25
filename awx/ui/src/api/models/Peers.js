import Base from '../Base';

class Peers extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/peers/';

    this.createPeer = this.createPeer.bind(this);
    this.destroyPeer = this.destroyPeer.bind(this);
  }

  createPeer(source_hostname, target_hostname) {
    return this.http.post(`${this.baseUrl}`, {
      source: source_hostname,
      target: target_hostname,
      link_state: 'established'
    });
  }

  async destroyPeer(source_hostname, target_hostname) {

    const { data } = await this.read({
      page: 1,
      page_size: 200,
      source__hostname__exact: source_hostname,
      target__hostname__exact: target_hostname,
    });

    const [peer_delete] = await Promise.all(
      data.results
        .map((peer) =>
          this.destroy(peer.id)
        )
    );
    return peer_delete;
  }

}

export default Peers;
