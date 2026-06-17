import cv2
import numpy as np
import base64
import tensorflow as tf
# Import các hàm custom để đưa vào custom_objects khi load model
from services.custom_metrics import weighted_sparse_cce, dice_coef_multiclass

class FaceAnalyzerService:
    def __init__(self, model_path):
        """Hàm khởi tạo: Chạy 1 lần duy nhất khi bật Server"""
        print("[AI Service] Đang tải mô hình UNet vào bộ nhớ...")
        self.model = tf.keras.models.load_model(
            model_path,
            compile=False,
            custom_objects={
                "weighted_sparse_cce": weighted_sparse_cce,
                "dice_coef_multiclass": dice_coef_multiclass,
                "iou_coef_multiclass": iou_coef_multiclass,
                "pixel_accuracy": pixel_accuracy,
                "sensitivity_multiclass": sensitivity_multiclass
            }
        )
        # Load mô hình cắt khuôn mặt của OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        print("[AI Service] Tải mô hình thành công!")

    def process_image(self, base64_image):
        """
        Luồng xử lý chính: Base64 -> Cắt Mặt -> AI Predict -> Mapping 5x5 -> Base64
        Trả về: tuple (success, data_dict, error_message)
        """
        try:
            # 1. Giải mã Base64
            chuoi_anh = base64_image.split(',')[1]
            img_bytes = base64.b64decode(chuoi_anh)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img_raw = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # 2. Nhận diện và cắt khuôn mặt (Padding 15%)
            gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(50, 50))
            
            if len(faces) == 0:
                return False, None, "Không nhận diện được khuôn mặt!"
                
            faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
            x, y, w, h = faces[0]
            pad_w, pad_h = int(w * 0.15), int(h * 0.15)
            img_process = img_raw[max(0, y - pad_h):min(img_raw.shape[0], y + h + pad_h), 
                                  max(0, x - pad_w):min(img_raw.shape[1], x + w + pad_w)]

            # 3. Chạy U-Net Inference
            img_resized = cv2.resize(cv2.cvtColor(img_process, cv2.COLOR_BGR2RGB), (256, 256), interpolation=cv2.INTER_AREA)
            img_input = np.expand_dims(img_resized.astype(np.float32) / 255.0, axis=0)
            pred = self.model.predict(img_input, verbose=0)[0]
            mask_256 = np.argmax(pred, axis=-1).astype(np.uint8)

            # 4. Logic Mapping Lưới 5x5 (Thuật toán lõi)
            led_grid, bright_grid = [0] * 25, [0] * 25
            cell_size = 256 / 5.0

            for row in range(5):
                for col in range(5):
                    idx = row * 5 + col
                    cell_mask = mask_256[int(row * cell_size):int((row + 1) * cell_size), 
                                         int(col * cell_size):int((col + 1) * cell_size)]

                    p0, p1, p2 = np.sum(cell_mask == 1), np.sum(cell_mask == 2), np.sum(cell_mask == 3)
                    total_disease = p0 + p1 + p2

                    if total_disease > 0:
                        if p1 > 2:   led_grid[idx] = 2
                        elif p0 > 2: led_grid[idx] = 1
                        elif p2 > 2: led_grid[idx] = 3

                    disease_ratio = total_disease / (cell_size * cell_size)
                    if disease_ratio > 0.30:    bright_grid[idx] = 25
                    elif disease_ratio > 0.10:  bright_grid[idx] = 15
                    elif disease_ratio > 0.005: bright_grid[idx] = 2

            # 5. Vẽ Overlay và Grid 5x5
            face_h, face_w, _ = img_process.shape
            mask_resized = cv2.resize(mask_256, (face_w, face_h), interpolation=cv2.INTER_NEAREST)
            
            overlay = img_process.copy()
            overlay[mask_resized == 1] = [255, 0, 0]
            overlay[mask_resized == 2] = [0, 0, 255]
            overlay[mask_resized == 3] = [0, 255, 0]
            cv2.addWeighted(overlay, 0.5, img_process, 0.5, 0, img_process)

            for i in range(1, 5):
                cv2.line(img_process, (int(face_w / 5.0 * i), 0), (int(face_w / 5.0 * i), face_h), (200, 200, 200), 1)
                cv2.line(img_process, (0, int(face_h / 5.0 * i)), (face_w, int(face_h / 5.0 * i)), (200, 200, 200), 1)

            # Mã hóa lại thành Base64
            _, buffer = cv2.imencode('.png', img_process)
            result_base64 = f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

            return True, {
                "image": result_base64,
                "led_grid": led_grid,
                "bright_grid": bright_grid,
                "count": int(np.sum(np.array(bright_grid) > 0))
            }, None

        except Exception as e:
            return False, None, str(e)