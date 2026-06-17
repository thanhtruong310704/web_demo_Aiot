# import cv2
# import numpy as np
# import matplotlib.pyplot as plt
# import tensorflow as tf
#
# # =========================
# # 1. CUSTOM LOSS / METRIC
# # =========================
# def dice_coef(y_true, y_pred, smooth=1e-6):
#     y_true_f = tf.keras.backend.flatten(y_true)
#     y_pred_f = tf.keras.backend.flatten(y_pred)
#     intersection = tf.keras.backend.sum(y_true_f * y_pred_f)
#     return (2.0 * intersection + smooth) / (
#         tf.keras.backend.sum(y_true_f) + tf.keras.backend.sum(y_pred_f) + smooth
#     )
#
# def dice_loss(y_true, y_pred):
#     return 1.0 - dice_coef(y_true, y_pred)
#
# def focal_loss(y_true, y_pred, alpha=0.75, gamma=2.0):
#     y_pred = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)
#     bce = -(y_true * tf.math.log(y_pred) + (1.0 - y_true) * tf.math.log(1.0 - y_pred))
#     p_t = y_true * y_pred + (1.0 - y_true) * (1.0 - y_pred)
#     alpha_factor = y_true * alpha + (1.0 - y_true) * (1.0 - alpha)
#     modulating_factor = tf.pow(1.0 - p_t, gamma)
#     return tf.reduce_mean(alpha_factor * modulating_factor * bce)
#
# def focal_dice_loss(y_true, y_pred):
#     return focal_loss(y_true, y_pred) + dice_loss(y_true, y_pred)
#
# def iou_coef(y_true, y_pred, smooth=1e-6):
#     y_pred = tf.cast(y_pred > 0.5, tf.float32)
#     intersection = tf.reduce_sum(y_true * y_pred, axis=[1, 2, 3])
#     union = tf.reduce_sum(y_true + y_pred, axis=[1, 2, 3]) - intersection
#     return tf.reduce_mean((intersection + smooth) / (union + smooth))
#
# # =========================
# # 2. CONFIG
# # =========================
# MODEL_PATH = r"D:\UNet\model_train_finish\model_synthetic_1.keras"
# TEST_IMAGE_PATH = r"D:\UNet\model_train_finish\test 3.jpg"
# SAVE_MASK_PATH = r"D:\UNet\model_train_finish\pred_mask.png"
# SAVE_OVERLAY_PATH = r"D:\UNet\model_train_finish\pred_overlay.png"
#
# IMG_SIZE = 512
# THRESHOLD = 0.5
#
# # =========================
# # 3. LOAD MODEL
# # =========================
# model = tf.keras.models.load_model(
#     MODEL_PATH,
#     custom_objects={
#         'focal_dice_loss': focal_dice_loss,
#         'dice_coef': dice_coef,
#         'iou_coef': iou_coef
#     }
# )
#
# print("Đã load model:", MODEL_PATH)
#
# # =========================
# # 4. LOAD + PREPROCESS IMAGE
# # =========================
# def load_rgb_image(image_path, img_size=512):
#     img = cv2.imread(image_path)
#     if img is None:
#         raise ValueError(f"Không đọc được ảnh: {image_path}")
#
#     img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#
#     # resize về đúng kích thước model cần
#     img_resized = cv2.resize(img, (img_size, img_size), interpolation=cv2.INTER_AREA)
#     img_resized = img_resized.astype(np.float32) / 255.0
#
#     return img_resized
#
# # =========================
# # 5. PREDICT
# # =========================
# def predict_image(model, image_rgb, threshold=0.5):
#     pred = model.predict(np.expand_dims(image_rgb, axis=0), verbose=0)[0]
#     pred_prob = pred.squeeze()
#     pred_bin = (pred_prob > threshold).astype(np.uint8)
#     return pred_prob, pred_bin
#
# # =========================
# # 6. SAVE OUTPUTS
# # =========================
# def save_outputs(image_rgb, pred_bin):
#     # lưu mask dự đoán
#     cv2.imwrite(SAVE_MASK_PATH, pred_bin * 255)
#
#     # tạo overlay
#     overlay = (image_rgb * 255).astype(np.uint8).copy()
#     red_mask = np.zeros_like(overlay)
#     red_mask[:, :, 0] = pred_bin * 255
#     overlay = cv2.addWeighted(overlay, 0.5, red_mask, 0, 0)
#
#     cv2.imwrite(SAVE_OVERLAY_PATH, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
#
# # =========================
# # 7. TEST 1 IMAGE
# # =========================
# image_rgb = load_rgb_image(TEST_IMAGE_PATH, IMG_SIZE)
# pred_prob, pred_bin = predict_image(model, image_rgb, THRESHOLD)
#
# plt.figure(figsize=(16, 4))
#
# plt.subplot(1, 4, 1)
# plt.imshow(image_rgb)
# plt.title("Input Image")
# plt.axis("off")
#
# plt.subplot(1, 4, 2)
# plt.imshow(pred_prob, cmap="gray")
# plt.title("Prediction Prob")
# plt.axis("off")
#
# plt.subplot(1, 4, 3)
# plt.imshow(pred_bin, cmap="gray")
# plt.title("Prediction Binary")
# plt.axis("off")
#
# plt.subplot(1, 4, 4)
# plt.imshow(image_rgb)
# plt.imshow(pred_bin, cmap="jet", alpha=0.5)
# plt.title("Overlay")
# plt.axis("off")
#
# plt.show()
#
# print("Pred min :", pred_prob.min())
# print("Pred max :", pred_prob.max())
# print("Pred mean:", pred_prob.mean())
#
# save_outputs(image_rgb, pred_bin)
#
# print("Đã lưu mask tại   :", SAVE_MASK_PATH)
# print("Đã lưu overlay tại:", SAVE_OVERLAY_PATH)

##########################################################################

import cv2
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

# =========================
# 1. CUSTOM LOSS / METRIC CHO MULTICLASS
# =========================
CLASS_WEIGHTS = tf.constant([0.05, 4.0, 5.0, 5.0], dtype=tf.float32)
NUM_CLASSES = 4
IMG_SIZE = 256   # model train với 256x256

def weighted_sparse_cce(y_true, y_pred):
    y_true = tf.cast(tf.squeeze(y_true, axis=-1), tf.int32)
    scce = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred)
    weights = tf.gather(CLASS_WEIGHTS, y_true)
    return tf.reduce_mean(scce * weights)

def dice_coef_multiclass(y_true, y_pred, num_classes=4, smooth=1e-6):
    y_true = tf.cast(tf.squeeze(y_true, axis=-1), tf.int32)
    y_true_onehot = tf.one_hot(y_true, depth=num_classes)

    y_pred_label = tf.argmax(y_pred, axis=-1)
    y_pred_onehot = tf.one_hot(tf.cast(y_pred_label, tf.int32), depth=num_classes)

    dices = []
    for c in range(1, num_classes):
        y_t = tf.reshape(tf.cast(y_true_onehot[..., c], tf.float32), [-1])
        y_p = tf.reshape(tf.cast(y_pred_onehot[..., c], tf.float32), [-1])

        intersection = tf.reduce_sum(y_t * y_p)
        denom = tf.reduce_sum(y_t) + tf.reduce_sum(y_p)
        dice = (2.0 * intersection + smooth) / (denom + smooth)
        dices.append(dice)

    return tf.reduce_mean(dices)

def iou_coef_multiclass(y_true, y_pred, num_classes=4, smooth=1e-6):
    y_true = tf.cast(tf.squeeze(y_true, axis=-1), tf.int32)
    y_true_onehot = tf.one_hot(y_true, depth=num_classes)

    y_pred_label = tf.argmax(y_pred, axis=-1)
    y_pred_onehot = tf.one_hot(tf.cast(y_pred_label, tf.int32), depth=num_classes)

    ious = []
    for c in range(1, num_classes):
        y_t = tf.reshape(tf.cast(y_true_onehot[..., c], tf.float32), [-1])
        y_p = tf.reshape(tf.cast(y_pred_onehot[..., c], tf.float32), [-1])

        intersection = tf.reduce_sum(y_t * y_p)
        union = tf.reduce_sum(y_t) + tf.reduce_sum(y_p) - intersection
        iou = (intersection + smooth) / (union + smooth)
        ious.append(iou)

    return tf.reduce_mean(ious)

# =========================
# 2. CONFIG
# =========================
MODEL_PATH = r"D:\UNet\train_3_classes_2\model_train\best_unet_multiclass_5.keras"
TEST_IMAGE_PATH = r"D:\UNet\train_3_classes_2\model_train\test 3.jpg"

# =========================
# 3. LOAD MODEL
# =========================
model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={
        "weighted_sparse_cce": weighted_sparse_cce,
        "dice_coef_multiclass": dice_coef_multiclass,
        "iou_coef_multiclass": iou_coef_multiclass
    }
)

print("Đã load model:", MODEL_PATH)
print("Input shape của model:", model.input_shape)

# =========================
# 4. LOAD + PREPROCESS IMAGE
# không crop, chỉ resize về 256x256
# =========================
def load_rgb_image(image_path, img_size=256):
    img_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError(f"Không đọc được ảnh: {image_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # giữ ảnh gốc để hiển thị
    original_rgb = img_rgb.copy()

    # resize đúng theo kích thước train
    img_resized = cv2.resize(img_rgb, (img_size, img_size), interpolation=cv2.INTER_AREA)
    img_input = img_resized.astype(np.float32) / 255.0

    return original_rgb, img_resized, img_input

# =========================
# 5. LABEL -> COLOR MASK
# =========================
def label_to_color_mask(label_mask):
    color = np.zeros((label_mask.shape[0], label_mask.shape[1], 3), dtype=np.uint8)

    # 1 = acne = blue
    color[label_mask == 1] = [0, 0, 255]

    # 2 = hsv = red
    color[label_mask == 2] = [255, 0, 0]

    # 3 = pigmentation = green
    color[label_mask == 3] = [0, 255, 0]

    return color

# =========================
# 6. PREDICT 1 IMAGE
# =========================
def predict_image_multiclass(model, image_input):
    pred = model.predict(np.expand_dims(image_input, axis=0), verbose=0)[0]  # (256,256,4)
    pred_label = np.argmax(pred, axis=-1).astype(np.uint8)
    pred_conf = np.max(pred, axis=-1)
    return pred, pred_label, pred_conf

# =========================
# 7. TEST 1 IMAGE
# =========================
original_rgb, image_rgb_resized, image_input = load_rgb_image(TEST_IMAGE_PATH, IMG_SIZE)
pred_softmax, pred_label, pred_conf = predict_image_multiclass(model, image_input)
pred_color = label_to_color_mask(pred_label)

# =========================
# 8. HIỂN THỊ
# =========================
plt.figure(figsize=(20, 5))

plt.subplot(1, 4, 1)
plt.imshow(original_rgb)
plt.title("Original Image")
plt.axis("off")

plt.subplot(1, 4, 2)
plt.imshow(image_rgb_resized)
plt.title("Resized 256x256")
plt.axis("off")

plt.subplot(1, 4, 3)
plt.imshow(pred_color)
plt.title("Prediction Mask")
plt.axis("off")

plt.subplot(1, 4, 4)
plt.imshow(image_rgb_resized)
plt.imshow(pred_color, alpha=0.4)
plt.title("Overlay")
plt.axis("off")

plt.tight_layout()
plt.show()

# =========================
# 9. IN THÔNG TIN
# =========================
unique_classes = np.unique(pred_label)
class_names = {
    0: "background",
    1: "acne",
    2: "hsv",
    3: "pigmentation"
}

print("Các class dự đoán có trong ảnh:", unique_classes)
for c in unique_classes:
    print(f"Class {c}: {class_names.get(int(c), 'unknown')}")

print("Softmax min :", pred_softmax.min())
print("Softmax max :", pred_softmax.max())
print("Conf min    :", pred_conf.min())
print("Conf max    :", pred_conf.max())
print("Conf mean   :", pred_conf.mean())

for cls_id in range(NUM_CLASSES):
    count = np.sum(pred_label == cls_id)
    print(f"Số pixel class {cls_id} ({class_names[cls_id]}): {count}")