import gz.math
import gz.sim
from gz.msgs.double_pb2 import Double
import gz.transport


class ZoomController:
    def __init__(self):
        self.node = gz.transport.Node()
        self.target_zoom = 1.0
        self.base_fov = 1.74
        self.zoom_changed = False

    # PythonSystemLoader once burayi cagirir
    def configure(self, entity, sdf, ecm, event_mgr):
        if sdf.has_element("base_fov"):
            self.base_fov = sdf.get_element("base_fov").get_double()

        topic = "/kamera/zoom_cmd"
        if sdf.has_element("zoom_topic"):
            topic = sdf.get_element("zoom_topic").get_string()

        # DIKKAT: subscribe imzasi -> (MesajTipi, topic, callback)
        self.node.subscribe(Double, topic, self.on_zoom_cmd)
        print(f"[ZoomController] aktif. topic: {topic}")

    def on_zoom_cmd(self, msg):
        self.target_zoom = max(1.0, msg.data)
        self.zoom_changed = True

    # ISystemPreUpdate karsiligi
    def pre_update(self, info, ecm):
        if not self.zoom_changed:
            return
        self.zoom_changed = False

        entities = ecm.entities_by_components(gz.sim.components.Camera())
        for e in entities:
            cam_comp = ecm.component(e, gz.sim.components.Camera())
            if cam_comp:
                cam_sdf = cam_comp.data()
                new_fov = self.base_fov / self.target_zoom
                cam_sdf.set_horizontal_fov(gz.math.Angle(new_fov))
                cam_comp.set_data(cam_sdf)
                ecm.set_changed(
                    e,
                    gz.sim.components.Camera.type_id(),
                    gz.sim.ComponentState.OneDimensionalChange,
                )


# PythonSystemLoader'in aradigi zorunlu fonksiyon
def get_system():
    return ZoomController()
