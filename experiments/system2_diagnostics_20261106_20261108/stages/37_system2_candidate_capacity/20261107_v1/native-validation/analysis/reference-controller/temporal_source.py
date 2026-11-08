"""Episode-local RGB change proposals. No category or held-object claims."""
import cv2
import numpy as np


class TemporalSource:
    def __init__(self, rgb, source_box, category):
        self.before = np.asarray(rgb).copy()
        self.source_box = np.asarray(source_box, dtype=float).copy()
        self.category = category
        center = (self.source_box[:2] + self.source_box[2:]) / 2
        size = max(self.source_box[2:] - self.source_box[:2]) * 1.25
        lo = np.maximum(0, center - size/2).astype(int)
        hi = np.minimum([rgb.shape[1], rgb.shape[0]], center + size/2).astype(int)
        self.crop = self.before[lo[1]:hi[1], lo[0]:hi[0]].copy()
        self.feature = None

    def supports_category(self, similarities, source_cosine, classes):
        target = classes.index(self.category)
        # Current semantics must independently agree; appearance cannot relabel.
        return bool(source_cosine >= .80 and int(np.argmax(similarities)) == target)

    def boxes(self, rgb):
        current = np.asarray(rgb)
        if current.shape != self.before.shape:
            return []
        changed = (np.abs(current.astype(np.int16) - self.before.astype(np.int16)).mean(axis=2) > 30).astype(np.uint8)
        roi = np.zeros(changed.shape, np.uint8)
        # Same public head tabletop/recovery region as registered; never new geometry.
        roi[212:395, 85:555] = changed[212:395, 85:555]
        roi = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        _, _, stats, _ = cv2.connectedComponentsWithStats(roi)
        result = []
        for x, y, w, h, area in stats[1:]:
            if area < 35 or max(w, h) > 110 or min(w, h) < 3 or area > 6500:
                continue
            box = np.asarray([x - 2, y - 2, x + w + 2, y + h + 2], dtype=float)
            overlap = np.maximum(0, np.minimum(box[2:], self.source_box[2:]) - np.maximum(box[:2], self.source_box[:2])).prod()
            # The old source footprint may now be bare table. Do not propose it
            # solely because its pixels changed after a pick.
            if overlap / max(1, (box[2:] - box[:2]).prod()) > .5:
                continue
            result.append(box)
        return result


def stable_pair(previous, current, category):
    """Match same-category current proposals across two actual observations."""
    stable = []
    for obj in current:
        if obj['category'] != category:
            continue
        box = np.asarray(obj['box'])
        center = (box[:2] + box[2:]) / 2
        size = np.maximum(1, box[2:] - box[:2])
        for old in previous:
            if old['category'] != category:
                continue
            old_box = np.asarray(old['box'])
            old_center = (old_box[:2] + old_box[2:]) / 2
            old_size = np.maximum(1, old_box[2:] - old_box[:2])
            if np.linalg.norm(center - old_center) <= 4 and np.all(np.abs(np.log(size / old_size)) <= .25):
                stable.append(obj)
                break
    return stable
