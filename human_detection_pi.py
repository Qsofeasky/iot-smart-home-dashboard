#!/usr/bin/env python3
import argparse
import sys
import time

import cv2
import numpy as np

PERSON_CLASS_ID = 0  # COCO class id for "person"


def parse_args():
    p = argparse.ArgumentParser(description="Human detection (OpenCV DNN, Pi-friendly)")
    p.add_argument("--source", default="0",
                   help="Camera index (0,1,...), video file path, or stream URL")
    p.add_argument("--model", default="yolov8n.onnx", help="Path to the exported ONNX model")
    p.add_argument("--imgsz", type=int, default=320,
                   help="Must match the imgsz used in export_to_onnx.py")
    p.add_argument("--conf", type=float, default=0.5, help="Confidence threshold")
    p.add_argument("--nms", type=float, default=0.45, help="NMS IoU threshold")
    p.add_argument("--headless", action="store_true",
                   help="Don't open a display window (use over SSH with no monitor)")
    p.add_argument("--save", default=None, help="Path to save annotated output video")
    p.add_argument("--no-print", action="store_true", help="Silence per-frame console logs")
    return p.parse_args()


def resolve_source(src):
    if src.isdigit():
        return int(src)
    return src


def letterbox(img, new_size, color=(114, 114, 114)):
    """Resize + pad image to a new_size x new_size square, keeping aspect ratio."""
    h, w = img.shape[:2]
    r = min(new_size / h, new_size / w)
    new_w, new_h = int(round(w * r)), int(round(h * r))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((new_size, new_size, 3), color, dtype=np.uint8)
    pad_x = (new_size - new_w) // 2
    pad_y = (new_size - new_h) // 2
    canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized
    return canvas, r, pad_x, pad_y


def detect_people(net, frame, imgsz, conf_thres, nms_thres):
    letterboxed, ratio, pad_x, pad_y = letterbox(frame, imgsz)

    blob = cv2.dnn.blobFromImage(letterboxed, scalefactor=1.0 / 255.0,
                                  size=(imgsz, imgsz), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward()  # shape: (1, 4+num_classes, num_anchors)

    preds = outputs[0].transpose()  # -> (num_anchors, 4+num_classes)
    class_scores = preds[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(len(class_scores)), class_ids]

    mask = (class_ids == PERSON_CLASS_ID) & (confidences >= conf_thres)
    preds = preds[mask]
    confidences = confidences[mask]

    boxes = []
    for cx, cy, w, h in preds[:, :4]:
        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        boxes.append([float(x1), float(y1), float(w), float(h)])

    results = []
    if len(boxes) > 0:
        indices = cv2.dnn.NMSBoxes(boxes, confidences.tolist(), conf_thres, nms_thres)
        if len(indices) > 0:
            indices = np.array(indices).flatten()
            for i in indices:
                x1, y1, w, h = boxes[i]
                x1 = (x1 - pad_x) / ratio
                y1 = (y1 - pad_y) / ratio
                w = w / ratio
                h = h / ratio
                x2, y2 = x1 + w, y1 + h
                results.append((x1, y1, x2, y2, float(confidences[i])))

    return results


def main():
    args = parse_args()

    print("Loading ONNX model: %s" % args.model)
    net = cv2.dnn.readNetFromONNX(args.model)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    source = resolve_source(args.source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print("ERROR: could not open video source '%s'" % args.source)
        sys.exit(1)

    writer = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 20.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        writer = cv2.VideoWriter(args.save, fourcc, fps_in, (w, h))
        print("Saving annotated output to: %s" % args.save)

    prev_time = time.time()
    fps_smooth = 0.0

    print("Running. Press 'q' to quit (display mode) or Ctrl+C to stop (headless mode).")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Stream ended or camera read failed.")
                break

            detections = detect_people(net, frame, args.imgsz, args.conf, args.nms)

            for (x1, y1, x2, y2, conf) in detections:
                p1 = (int(x1), int(y1))
                p2 = (int(x2), int(y2))
                cv2.rectangle(frame, p1, p2, (0, 255, 0), 2)
                label = "person %.2f" % conf
                cv2.putText(frame, label, (p1[0], max(p1[1] - 8, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            now = time.time()
            inst_fps = 1.0 / max(now - prev_time, 1e-6)
            fps_smooth = inst_fps if fps_smooth == 0 else 0.9 * fps_smooth + 0.1 * inst_fps
            prev_time = now

            cv2.putText(frame, "FPS: %.1f  People: %d" % (fps_smooth, len(detections)),
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if not args.no_print:
                print("FPS: %5.1f | People detected: %d" % (fps_smooth, len(detections)))

            if writer:
                writer.write(frame)

            if not args.headless:
                cv2.imshow("Human Detection (press q to quit)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        cap.release()
        if writer:
            writer.release()
        if not args.headless:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
