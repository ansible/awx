import Base from '../Base';

class Mesh extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/mesh_visualizer/';
  }
}
export default Mesh;
