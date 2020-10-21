import numpy as np
import itertools


def corners(bbox):
    """Get the corners of a box in N-dim"""
    mins = bbox[::2]
    maxs = bbox[1::2]
    return list(itertools.product(*zip(mins, maxs)))


class Union:
    def __init__(self, domains):
        geom_dim = [d.dim for d in domains]
        assert np.all(geom_dim != 2) or np.all(geom_dim != 3)
        self.dim = geom_dim[0]
        if self.dim == 2:
            self.bbox = (
                min(d.bbox[0] for d in domains),
                max(d.bbox[1] for d in domains),
                min(d.bbox[2] for d in domains),
                max(d.bbox[3] for d in domains),
            )
        elif self.dim == 3:
            self.bbox = (
                min(d.bbox[0] for d in domains),
                max(d.bbox[1] for d in domains),
                min(d.bbox[2] for d in domains),
                max(d.bbox[3] for d in domains),
                max(d.bbox[4] for d in domains),
                max(d.bbox[5] for d in domains),
            )
        self.corners = corners(self.bbox)
        self.domains = domains

    def eval(self, x):
        return np.minimum.reduce([d.eval(x) for d in self.domains])


class Intersection:
    def __init__(self, domains):
        geom_dim = [d.dim for d in domains]
        assert np.all(geom_dim != 2) or np.all(geom_dim != 3)
        self.dim = geom_dim[0]
        if self.dim == 2:
            self.bbox = (
                min(d.bbox[0] for d in domains),
                max(d.bbox[1] for d in domains),
                min(d.bbox[2] for d in domains),
                max(d.bbox[3] for d in domains),
            )
        elif self.dim == 3:
            self.bbox = (
                min(d.bbox[0] for d in domains),
                max(d.bbox[1] for d in domains),
                min(d.bbox[2] for d in domains),
                max(d.bbox[3] for d in domains),
                max(d.bbox[4] for d in domains),
                max(d.bbox[5] for d in domains),
            )
        self.corners = corners(self.bbox)
        self.domains = domains

    def eval(self, x):
        return np.maximum.reduce([d.eval(x) for d in self.domains])


class Difference:
    def __init__(self, domains):
        geom_dim = [d.dim for d in domains]
        assert np.all(geom_dim != 2) or np.all(geom_dim != 3)
        self.dim = geom_dim[0]
        if self.dim == 2:
            self.bbox = (
                min(d.bbox[0] for d in domains),
                max(d.bbox[1] for d in domains),
                min(d.bbox[2] for d in domains),
                max(d.bbox[3] for d in domains),
            )
        elif self.dim == 3:
            self.bbox = (
                min(d.bbox[0] for d in domains),
                max(d.bbox[1] for d in domains),
                min(d.bbox[2] for d in domains),
                max(d.bbox[3] for d in domains),
                max(d.bbox[4] for d in domains),
                max(d.bbox[5] for d in domains),
            )
        self.corners = corners(self.bbox)
        self.domains = domains

    def eval(self, x):
        return np.maximum.reduce(
            [-d.eval(x) if n > 0 else d.eval(x) for n, d in enumerate(self.domains)]
        )


class Disk:
    def __init__(self, x0, r):
        self.dim = 2
        self.corners = None
        self.xc = x0[0]
        self.yc = x0[1]
        self.r = r
        self.bbox = (x0[0] - r, x0[0] + r, x0[1] - r, x0[1] + r)

    def eval(self, x):
        return _ddisk(x, self.xc, self.yc, self.r)


class Rectangle:
    def __init__(self, bbox):
        self.dim = 2
        self.corners = corners(bbox)
        self.bbox = bbox

    def eval(self, x):
        return drectangle(x, *self.bbox)


class Cube:
    def __init__(self, bbox):
        self.dim = 3
        self.corners = corners(bbox)
        self.bbox = bbox

    def eval(self, x):
        return dblock(x, *self.bbox)


def _ddisk(p, xc, yc, r):
    """Signed distance to disk centered at xc, yc with radius r."""
    return np.sqrt(((p - np.array([xc, yc])) ** 2).sum(-1)) - r


def drectangle(p, x1, x2, y1, y2):
    min = np.minimum
    """Signed distance function for rectangle with corners (x1,y1), (x2,y1),
    (x1,y2), (x2,y2).
    This has an incorrect distance to the four corners but that isn't a big deal
    """
    return -min(min(min(-y1 + p[:, 1], y2 - p[:, 1]), -x1 + p[:, 0]), x2 - p[:, 0])


def dblock0(p, x1, x2, y1, y2, z1, z2):
    # adapted from:
    # https://github.com/nschloe/dmsh/blob/3305c417d373d509c78491b24e77409411aa18c2/dmsh/geometry/rectangle.py#L31
    # outside dist
    # https://gamedev.stackexchange.com/a/44496
    w = x2 - x1
    h = y2 - y1
    d = z2 - z1
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    cz = (z1 + z2) / 2
    dx = np.abs(p[:, 0] - cx) - w / 2
    dy = np.abs(p[:, 1] - cy) - h / 2
    dz = np.abs(p[:, 2] - cz) - d / 2
    is_inside = (dx <= 0) & (dy <= 0) & (dz <= 0)
    dx[dx < 0.0] = 0.0
    dy[dy < 0.0] = 0.0
    dz[dz < 0.0] = 0.0
    dist = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
    # inside dist
    a = np.array(
        [
            p[is_inside, 0] - x1,
            x2 - p[is_inside, 0],
            p[is_inside, 1] - y1,
            y2 - p[is_inside, 1],
            p[is_inside, 2] - z1,
            z2 - p[is_inside, 2],
        ]
    )
    dist[is_inside] = -np.min(a, axis=0)
    return dist


def dblock(p, x1, x2, y1, y2, z1, z2):
    min = np.minimum
    return -min(
        min(
            min(min(min(-z1 + p[:, 2], z2 - p[:, 2]), -y1 + p[:, 1]), y2 - p[:, 1]),
            -x1 + p[:, 0],
        ),
        x2 - p[:, 0],
    )
