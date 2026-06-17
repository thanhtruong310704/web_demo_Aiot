import tensorflow as tf

# Trọng số phạt cho bài toán mất cân bằng lớp y tế
CLASS_WEIGHTS = tf.constant([0.05, 4.0, 5.0, 5.0], dtype=tf.float32)

@tf.keras.utils.register_keras_serializable()
def weighted_sparse_cce(y_true, y_pred):
    y_true = tf.cast(tf.squeeze(y_true, axis=-1), tf.int32)
    scce = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred)
    weights = tf.gather(CLASS_WEIGHTS, y_true)
    return tf.reduce_mean(scce * weights)

@tf.keras.utils.register_keras_serializable()
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

@tf.keras.utils.register_keras_serializable()
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

@tf.keras.utils.register_keras_serializable()
def pixel_accuracy(y_true, y_pred):
    y_true = tf.cast(tf.squeeze(y_true, axis=-1), tf.int32)
    y_pred_label = tf.cast(tf.argmax(y_pred, axis=-1), tf.int32)
    correct_pixels = tf.cast(tf.equal(y_true, y_pred_label), tf.float32)
    return tf.reduce_mean(correct_pixels)

@tf.keras.utils.register_keras_serializable()
def sensitivity_multiclass(y_true, y_pred, num_classes=4, smooth=1e-6):
    y_true = tf.cast(tf.squeeze(y_true, axis=-1), tf.int32)
    y_true_onehot = tf.one_hot(y_true, depth=num_classes)
    y_pred_label = tf.argmax(y_pred, axis=-1)
    y_pred_onehot = tf.one_hot(tf.cast(y_pred_label, tf.int32), depth=num_classes)
    sensitivities = []
    for c in range(1, num_classes):
        y_t = tf.reshape(tf.cast(y_true_onehot[..., c], tf.float32), [-1])
        y_p = tf.reshape(tf.cast(y_pred_onehot[..., c], tf.float32), [-1])
        tp = tf.reduce_sum(y_t * y_p)
        tp_plus_fn = tf.reduce_sum(y_t)
        sen = (tp + smooth) / (tp_plus_fn + smooth)
        sensitivities.append(sen)
    return tf.reduce_mean(sensitivities)