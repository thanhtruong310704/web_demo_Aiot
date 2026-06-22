import cv2
import numpy as np
import base64
import tensorflow as tf
from services.custom_metrics import weighted_sparse_cce, dice_coef_multiclass, pixel_accuracy, sensitivity_multiclass, iou_coef_multiclass

class FaceAnalyzerService:
    def __init__(self, model_path):
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
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        print("[AI Service] Tải mô hình thành công!")

    def process_image(self, base64_image):
        try:
            # 1. Giải mã Base64 thành ảnh OpenCV
            chuoi_anh = base64_image.split(',')[1]
            img_bytes = base64.b64decode(chuoi_anh)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img_raw = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # 2. Nhận diện và cắt khuôn mặt
            gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(50, 50))
             
            if len(faces) == 0:
                return False, None, "Không nhận diện được khuôn mặt! Vui lòng đưa mặt vào giữa khung hình hoặc chọn ảnh khác."
                
            faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
            x, y, w, h = faces[0]
            
            pad_w = int(w * 0.15)
            pad_h = int(h * 0.15)
            
            y1 = max(0, y - pad_h)
            y2 = min(img_raw.shape[0], y + h + pad_h)
            x1 = max(0, x - pad_w)
            x2 = min(img_raw.shape[1], x + w + pad_w)

            img_process = img_raw[y1:y2, x1:x2].copy()

            # 3. Chạy U-Net Inference
            img_rgb = cv2.cvtColor(img_process, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (256, 256), interpolation=cv2.INTER_AREA)
            
            img_input = img_resized.astype(np.float32) / 255.0
            img_input = np.expand_dims(img_input, axis=0)
            
            pred = self.model.predict(img_input, verbose=0)[0]
            mask_256 = np.argmax(pred, axis=-1).astype(np.uint8)

            # Chuyển từ RGB về BGR để lưu màu đúng chuẩn OpenCV
            img_resized_bgr = cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR)
            _, buffer_resized = cv2.imencode('.png', img_resized_bgr)
            resized_base64 = f"data:image/png;base64,{base64.b64encode(buffer_resized).decode('utf-8')}"

            # 4. Logic Mapping Lưới 5x5
            led_grid = [0] * 25
            bright_grid = [0] * 25
            cell_size = 256 / 5.0
            cell_area = cell_size * cell_size

            for row in range(5):
                for col in range(5):
                    idx = row * 5 + col
                    y_start, y_end = int(row * cell_size), int((row + 1) * cell_size)
                    x_start, x_end = int(col * cell_size), int((col + 1) * cell_size)

                    cell_mask = mask_256[y_start:y_end, x_start:x_end]

                    # p0 = np.sum(cell_mask == 1)
                    # p1 = np.sum(cell_mask == 2)
                    # p2 = np.sum(cell_mask == 3)

                    # total_disease_pixels = p0 + p1 + p2

                    # if total_disease_pixels > 0:
                    #     if p1 > 2:
                    #         led_grid[idx] = 2
                    #     elif p0 > 2:
                    #         led_grid[idx] = 1
                    #     elif p2 > 2:
                    #         led_grid[idx] = 3

                    # disease_ratio = total_disease_pixels / cell_area

                    # if disease_ratio > 0.25:
                    #     bright_grid[idx] = 25
                    # elif disease_ratio > 0.08:
                    #     bright_grid[idx] = 15
                    # elif disease_ratio > 0.005:
                    #     bright_grid[idx] = 2
                    # else:
                    #     bright_grid[idx] = 0
                    #     led_grid[idx] = 0
                    # Đếm nhanh số pixel của từng màu (Cách tối ưu)
                    counts = np.bincount(cell_mask.flatten(), minlength=4)
                    p0 = counts[1]  # Pixel màu Xanh biển
                    p1 = counts[2]  # Pixel màu Đỏ
                    p2 = counts[3]  # Pixel màu Xanh lá

                    active_pixels = 0  # Biến lưu số pixel của màu được chọn
                    led_color = 0      # Biến lưu ID màu LED

                    # 1. Quyết định màu LED và lấy số pixel của màu đó (theo thứ tự ưu tiên)
                    if p1 > 2:
                        led_color = 2
                        active_pixels = p1
                    elif p0 > 2:
                        led_color = 1
                        active_pixels = p0
                    elif p2 > 2:
                        led_color = 3
                        active_pixels = p2

                    # 2. Tính tỉ lệ dựa trên màu đã được chọn
                    if led_color != 0:
                        disease_ratio = active_pixels / cell_area
                        # 3. Phân mức độ sáng dựa trên tỉ lệ của màu đó
                        if disease_ratio > 0.06:
                            bright_grid[idx] = 25
                        elif disease_ratio > 0.03:
                            bright_grid[idx] = 15
                        elif disease_ratio > 0.005:
                            bright_grid[idx] = 2
                        else:
                            bright_grid[idx] = 0
                            led_color = 0  # Nếu tỉ lệ quá nhỏ (dưới 0.5%), tắt luôn LED
                    else:
                        bright_grid[idx] = 0

                    # Gán kết quả vào mảng
                    led_grid[idx] = led_color

            # 5. Vẽ Overlay màu bệnh lý
            face_h, face_w, _ = img_process.shape
            mask_resized = cv2.resize(mask_256, (face_w, face_h), interpolation=cv2.INTER_NEAREST)
            
            img_result = img_process.copy()
            overlay = img_process.copy()

            overlay[mask_resized == 1] = [255, 0, 0]
            overlay[mask_resized == 2] = [0, 0, 255]
            overlay[mask_resized == 3] = [0, 255, 0]

            cv2.addWeighted(overlay, 0.5, img_result, 0.5, 0, img_result)

            step_x = face_w / 5.0
            step_y = face_h / 5.0

            for i in range(1, 5):
                x_line = int(step_x * i)
                y_line = int(step_y * i)
                cv2.line(img_result, (x_line, 0), (x_line, face_h), (200, 200, 200), 1)
                cv2.line(img_result, (0, y_line), (face_w, y_line), (200, 200, 200), 1)

            # 6. Mã hóa lại thành Base64
            _, buffer = cv2.imencode('.png', img_result)
            result_base64 = f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

            return True, {
                "image": result_base64,
                "image_resized": resized_base64, # Đã thay đổi thành base64 thay vì numpy array
                "led_grid": led_grid,
                "bright_grid": bright_grid,
                "count": int(np.sum(np.array(bright_grid) > 0))
            }, None

        except Exception as e:
            return False, None, str(e)