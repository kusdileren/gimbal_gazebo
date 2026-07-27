#ifndef ZOOM_CONTROLLER_HH_
#define ZOOM_CONTROLLER_HH_

#include <mutex>
#include <string>

#include <gz/msgs/double.pb.h>
#include <gz/sim/System.hh>
#include <gz/transport/Node.hh>
#include <gz/rendering/RenderTypes.hh>
#include <gz/common/Event.hh>

namespace zoom_controller
{
  // Terminalden gelen zoom komutunu dinleyip render thread'inde
  // GERCEK gz-rendering Camera nesnesinin HFOV'unu degistiren plugin.
  // ECM/Camera-component mutasyonundan farkli olarak burada canli
  // render nesnesine dogrudan yaziyoruz, bu yuzden gorsel olarak calisir.
  class ZoomController :
      public gz::sim::System,
      public gz::sim::ISystemConfigure
  {
    public: void Configure(
        const gz::sim::Entity &_entity,
        const std::shared_ptr<const sdf::Element> &_sdf,
        gz::sim::EntityComponentManager &_ecm,
        gz::sim::EventManager &_eventMgr) override;

    // Rendering engine singleton uzerinden sahneyi bulur (resmi ornekle ayni)
    private: void FindScene();

    // PreRender eventinde (render thread'inde) cagrilir, kamerayi bulup
    // HFOV'u gunceller
    private: void PerformRenderingOperations();

    // gz-transport callback'i: /kamera/zoom_cmd'den gelen mesaji isler
    private: void OnZoomCmd(const gz::msgs::Double &_msg);

    private: gz::rendering::ScenePtr scene{nullptr};
    private: gz::rendering::CameraPtr camera{nullptr};

    private: gz::transport::Node node;
    private: gz::common::ConnectionPtr renderConnection;

    private: std::string cameraName{"imager"};
    private: double baseFov{1.74};

    private: std::mutex mutex;
    private: double targetZoom{1.0};
    private: bool zoomChanged{false};
  };
}  // namespace zoom_controller

#endif
