#include "ZoomController.hh"

#include <algorithm>
#include <functional>

#include <gz/msgs/double.pb.h>
#include <gz/plugin/Register.hh>

#include <gz/math/Angle.hh>

#include <gz/rendering/RenderingIface.hh>
#include <gz/rendering/RenderEngine.hh>
#include <gz/rendering/Scene.hh>
#include <gz/rendering/Camera.hh>

#include <gz/sim/rendering/Events.hh>
#include <gz/common/Console.hh>

using namespace zoom_controller;

//////////////////////////////////////////////////
void ZoomController::Configure( // sdf değerlerini okur ve dinlenecek topicğe abone olur.
    const gz::sim::Entity & /*_entity*/,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager & /*_ecm*/,
    gz::sim::EventManager &_eventMgr)
{
  if (_sdf->HasElement("base_fov"))
    this->baseFov = _sdf->Get<double>("base_fov");

  if (_sdf->HasElement("camera_name"))
    this->cameraName = _sdf->Get<std::string>("camera_name");

  std::string topic = "/kamera/zoom_cmd";
  if (_sdf->HasElement("zoom_topic"))
    topic = _sdf->Get<std::string>("zoom_topic");

  // gz-transport uzerinden zoom komutlarina abone ol (ROS bridge buraya yazacak)
  this->node.Subscribe(topic, &ZoomController::OnZoomCmd, this);

  // Render thread'inde her karede tetiklenecek callback'i bagla.
  // ISTEDIGIMIZ SEY BU: canli kamera nesnesine yalnizca bu thread'de
  // dokunmak guvenli.
  this->renderConnection = _eventMgr.Connect<gz::sim::events::PreRender>(
      std::bind(&ZoomController::PerformRenderingOperations, this)); //her render karesinde çalışacak fonksiyon bağlanıyor.

  gzmsg << "[ZoomController] hazir. topic: " << topic
        << " kamera: " << this->cameraName
        << " base_fov: " << this->baseFov << std::endl;
}

//////////////////////////////////////////////////
void ZoomController::OnZoomCmd(const gz::msgs::Double &_msg) // dışarıdan zoom iteği geldiğinde tetiklenir ve target zoomu çalıştırır. 
{
  std::lock_guard<std::mutex> lock(this->mutex);
  this->targetZoom = std::max(1.0, _msg.data());
  this->zoomChanged = true;
}

////////////////////////////////////////////////// findscene ve performRenderingOperations render thread'inde çalışacak fonksiyonlar. 
//findscene sahneyi bulur, performRenderingOperations ise kamerayı bulup HFOV'u günceller.
void ZoomController::FindScene()
{
  auto loadedEngNames = gz::rendering::loadedEngines();
  if (loadedEngNames.empty())
  {
    gzdbg << "[ZoomController] henuz render engine yuklenmedi" << std::endl;
    return;
  }

  auto engineName = loadedEngNames[0];
  auto engine = gz::rendering::engine(engineName);
  if (!engine || engine->SceneCount() == 0)
    return;

  auto scenePtr = engine->SceneByIndex(0);
  if (!scenePtr || !scenePtr->IsInitialized() || !scenePtr->RootVisual())
    return;

  this->scene = scenePtr;
}

//////////////////////////////////////////////////
void ZoomController::PerformRenderingOperations()
{
  bool changed;
  double zoom;
  {
    std::lock_guard<std::mutex> lock(this->mutex);
    changed = this->zoomChanged;
    zoom = this->targetZoom;
    this->zoomChanged = false;
  }

  if (!changed)
    return;

  if (nullptr == this->scene)
    this->FindScene();
  if (nullptr == this->scene)
    return;

  if (nullptr == this->camera)
  {
    // 1. Önce tam isimle bulmayı deneriz
    auto sensor = this->scene->SensorByName(this->cameraName);
    
    // 2. Eğer tam isimle bulamazsa, dünyadaki tüm sensörleri tarar ve 
    // isminin içinde "imager" (veya cameraName neyse) geçen ilk sensörü alır
    if (!sensor) {
      for (unsigned int i = 0; i < this->scene->SensorCount(); ++i) {
        auto s = this->scene->SensorByIndex(i);
        if (s->Name().find(this->cameraName) != std::string::npos) {
          sensor = s;
          break;
        }
      }
    }

    this->camera = std::dynamic_pointer_cast<gz::rendering::Camera>(sensor);
    
    // 3. Hala bulamadıysa, sistemdeki sensörleri yazdırarak hata basar
    if (nullptr == this->camera)
    {
      gzerr << "[ZoomController] kamera bulunamadi. Aranan kelime: " 
            << this->cameraName << std::endl;
            
      // Debug için dünyadaki mevcut sensör isimlerini konsola bastırır
      gzerr << "Mevcut olan sensorler:" << std::endl;
      for (unsigned int i = 0; i < this->scene->SensorCount(); ++i) {
          gzerr << " - " << this->scene->SensorByIndex(i)->Name() << std::endl;
      }
      return;
    }
  }

  double newFov = this->baseFov / zoom;
  this->camera->SetHFOV(gz::math::Angle(newFov));
  gzmsg << "[ZoomController] FOV guncellendi -> zoom=" << zoom
        << " fov=" << newFov << std::endl;
}

GZ_ADD_PLUGIN(
    zoom_controller::ZoomController,
    gz::sim::System,
    gz::sim::ISystemConfigure)

GZ_ADD_PLUGIN_ALIAS(zoom_controller::ZoomController,
                     "zoom_controller::ZoomController")
