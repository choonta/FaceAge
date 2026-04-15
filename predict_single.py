#!/usr/bin/env python3
"""
Quick single-image FaceAge prediction.
Usage: python predict_single.py path/to/photo.jpg
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import sys
import json
import base64
import marshal
import tempfile
import PIL
import mtcnn
import numpy as np
import tensorflow as tf
import tf_keras as keras
import h5py

from skimage.io import imread

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PROJECT_PATH, "models", "faceage_model.h5")

# Recompiled Python 3.11 bytecode for: lambda inputs, scale: inputs[0] + inputs[1] * scale
_LAMBDA_FN = lambda inputs, scale: inputs[0] + inputs[1] * scale
_NEW_BYTECODE = base64.b64encode(marshal.dumps(_LAMBDA_FN.__code__)).decode()


def _patch_lambda_config(config):
    """Replace Python-version-specific Lambda bytecodes in the model config."""
    if isinstance(config, dict):
        if config.get('class_name') == 'Lambda':
            cfg = config.get('config', {})
            if isinstance(cfg.get('function'), list) and len(cfg['function']) == 3:
                cfg['function'][0] = _NEW_BYTECODE
        return {k: _patch_lambda_config(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_patch_lambda_config(v) for v in config]
    return config


def load_model_patched(model_path):
    """Load the legacy .h5 FaceAge model, patching Lambda bytecodes for Python 3.11+."""
    # Allow Lambda layer deserialization from trusted source
    from tf_keras.src.saving.serialization_lib import enable_unsafe_deserialization
    enable_unsafe_deserialization()

    with h5py.File(model_path, 'r') as f:
        raw_config = f.attrs['model_config']

    config = json.loads(raw_config)
    patched_config = _patch_lambda_config(config)

    model = keras.models.model_from_config(patched_config)
    model.load_weights(model_path)
    return model


## ----------------------------------------

def get_face_bbox(path_to_image):
    img = np.asarray(PIL.Image.open(path_to_image).convert('RGB'))
    try:
        return mtcnn.mtcnn.MTCNN().detect_faces(img)[0]
    except Exception as e:
        print(f"ERROR: Face detection failed for '{path_to_image}': {e}")
        return None


def predict_age(model, path_to_image, bbox):
    img = np.asarray(PIL.Image.open(path_to_image).convert('RGB'))
    x1, y1, width, height = bbox['box']
    x1, y1 = abs(x1), abs(y1)
    x2, y2 = x1 + width, y1 + height
    face = img[y1:y2, x1:x2]
    face_pil = PIL.Image.fromarray(np.uint8(face)).convert('RGB')
    face = np.asarray(face_pil.resize((160, 160)))
    mean, std = face.mean(), face.std()
    face = (face - mean) / std
    return float(np.squeeze(model.predict(face.reshape(1, 160, 160, 3))))


## ----------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python predict_single.py <path_to_image>")
        sys.exit(1)

    image_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        sys.exit(1)

    print(f"Image : {image_path}")
    print("Detecting face...")
    bbox = get_face_bbox(image_path)
    if bbox is None:
        print("No face detected.")
        sys.exit(1)
    print(f"Face detected (confidence: {bbox['confidence']:.3f})")

    print("Loading model...")
    model = load_model_patched(MODEL_PATH)

    print("Estimating age...")
    age = predict_age(model, image_path, bbox)
    print(f"\n>>> Estimated FaceAge: {age:.1f} years <<<\n")


if __name__ == "__main__":
    main()
