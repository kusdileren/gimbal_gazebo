import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64
from cv_bridge import CvBridge
import cv2

class GimbalTrackerNode(Node):
    def __init__(self):
        super().__init__('gimbal_tracker_node')
        
        self.bridge = CvBridge()
        
        
        self.yaw_pub = self.create_publisher(Float64, '/kule_yaw_cmd', 10)
        self.tilt_pub = self.create_publisher(Float64, '/kule_tilt_cmd', 10)
        
        self.image_sub = self.create_subscription(
            Image, 
            '/kamera/goruntu', 
            self.image_callback, 
            10
        )
        
        self.tracker = None
        self.is_tracking = False
        
        # Gimbal mevcut acilar
        self.current_yaw = 1.60
        self.current_tilt = 2.01
        
        self.kp_yaw = 0.0003
        self.kp_tilt = 0.0003
        
        self.drawing = False
        self.roi_start = (0, 0)
        self.roi_end = (0, 0)
        self.selection_ready = False

        
        self.window_name = "Gimbal Kamera Takip Arayuzu"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        #acilari yayinlayan kisim
        self.init_timer = self.create_timer(0.1, self.publish_initial_pose)
        
        self.get_logger().info("gimbal tracker basladi")
        self.get_logger().info("sol tusa basin ve kutu cizin")

    # nesne takibi yoksa kamera baslangic pozisyonunda sabit kalir.
    def publish_initial_pose(self):
        if not self.is_tracking:
            yaw_msg = Float64()
            yaw_msg.data = self.current_yaw
            self.yaw_pub.publish(yaw_msg)
            
            tilt_msg = Float64()
            tilt_msg.data = self.current_tilt
            self.tilt_pub.publish(tilt_msg)

    #kare cizimini saglar.
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.roi_start = (x, y)
            self.roi_end = (x, y)
            self.is_tracking = False #cizim yapilirken takip islemi durdurulur.
            self.selection_ready = False
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.roi_end = (x, y)
                
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.roi_end = (x, y)
            self.selection_ready = True # yeni hedef belirlendi durumunu saglar.

    #her yeni kare icin sisteme dosyalar yuklenir ve o yesil alanda tanir.
    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8') 
        #dikdortgene alinan her frame anlamlandirilarak  islemler onun uzerinden gider.
        
        if self.selection_ready:
            x1, y1 = self.roi_start
            x2, y2 = self.roi_end
            
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            if w > 10 and h > 10:  
                #cizilen dikdortgen x,y,w,h bicimine cevrilir <10 ise tekrar girilir
                self.tracker = cv2.TrackerCSRT_create()
                self.tracker.init(frame, (x, y, w, h))
                self.is_tracking = True
                self.get_logger().info("Yeni hedef kilitlendi!")
            
            self.selection_ready = False
            
            #eger dikdortgeni birakmdiysa secim yapiliyor der.
        if self.drawing:
            cv2.rectangle(frame, self.roi_start, self.roi_end, (255, 0, 0), 2)
            cv2.putText(frame, "Secim Yapiliyor...", (20, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        if self.is_tracking and self.tracker is not None:
            success, bbox = self.tracker.update(frame)
            #takip basladiysa arabanin yeni konumu aranir eger bulunursa yesil kutu cizilip 
            #devamli gider.
            
            if success:
                x, y, w, h = [int(v) for v in bbox]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                #arabanin merkezi hesaplanir
                obj_cx = x + w / 2.0
                obj_cy = y + h / 2.0
                
                #kameranin merkezi
                img_h, img_w, _ = frame.shape
                img_cx = img_w / 2.0
                img_cy = img_h / 2.0
                
                #hata goruntunun merkezi -arabanin merkezi arasindadir
                err_x = img_cx - obj_cx
                err_y = img_cy - obj_cy
                
                #hatalar sabit katsayi ile carpilir ve yaw ve tilt eklenir kamera hareketi icin
                self.current_yaw += self.kp_yaw * err_x
                self.current_tilt -= self.kp_tilt * err_y
                
                self.current_yaw = max(min(self.current_yaw, 3.1415), -3.1415)
                self.current_tilt = max(min(self.current_tilt, 3.1415), -0.1)
                
                yaw_msg = Float64()
                yaw_msg.data = self.current_yaw
                self.yaw_pub.publish(yaw_msg)
                
                tilt_msg = Float64()
                tilt_msg.data = self.current_tilt
                self.tilt_pub.publish(tilt_msg)
                
                cv2.putText(frame, "Takip Durumu: AKTIF", (20, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Takip Durumu: KAYBEDILDI", (20, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                self.is_tracking = False
        else:
            if not self.drawing:
                cv2.putText(frame, "Farenizle hedefi secin", (20, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
        cv2.imshow(self.window_name, frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = GimbalTrackerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()