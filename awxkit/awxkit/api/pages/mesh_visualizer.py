from awxkit.api.resources import resources
from . import base
from . import page


class MeshVisualizer(base.Base):

    pass


page.register_page(resources.mesh_visualizer, MeshVisualizer)
