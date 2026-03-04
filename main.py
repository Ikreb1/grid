from __future__ import annotations

epsilon = 1e-6

class Vector():
    def __init__(self, x: float=0.0, y: float=0.0, z: float=0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self) -> str:
        return f"x:{self.x} y:{self.y} z:{self.z}"
    
    def __mul__(self, other: float) -> Vector:
        return Vector(self.x * other, self.y * other, self.z * other)
    
    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector) -> Vector:
        return self + -other
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return (
            abs(self.x - other.x) <= epsilon
            and abs(self.y - other.y) <= epsilon
            and abs(self.z - other.z) <= epsilon
        )
    
    def __neg__(self) -> Vector:
        return self * -1
    
    def dot(self, other: Vector) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

class AttachmentPoint():
    def __init__(self, pos: Vector, bitangent: Vector, tangent: Vector, normal: Vector):
        # corner of plane
        self.pos = pos
        self.bitangent = bitangent
        self.tangent = tangent
        self.normal = normal
        self.is_attached = False

    def __repr__(self):
        return f"pos({self.pos}) dir({self.bitangent}) tan({self.tangent}) norm({self.normal})"
    
    def raycast(self, ray_direction: Vector, ray_origin: Vector) -> RayHit:
        ray_hit = RayHit(False, None)

        denominator = self.normal.dot(ray_direction)
        if abs(denominator) < epsilon:
            return ray_hit

        hit_distance = self.normal.dot(self.pos - ray_origin) / denominator
        if hit_distance < 0:
            return ray_hit

        hit_point = ray_origin + (ray_direction * hit_distance)
        hit_offset = hit_point - self.pos

        tangent_length_sq = self.tangent.dot(self.tangent)
        bitangent_length_sq = self.bitangent.dot(self.bitangent)
        if tangent_length_sq < epsilon or bitangent_length_sq < epsilon:
            return ray_hit

        u = hit_offset.dot(self.bitangent) / bitangent_length_sq
        v = hit_offset.dot(self.tangent) / tangent_length_sq

        if 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0:
            ray_hit.hit = True
            ray_hit.hit_point = hit_point
            ray_hit.distance = hit_distance
        return ray_hit

    def validate(self):
        # Orthogonality test: two vectors are 90° apart when their dot product is approximately 0.
        return (
            abs(self.tangent.dot(self.normal)) <= epsilon
            and abs(self.tangent.dot(self.bitangent)) <= epsilon
            and abs(self.normal.dot(self.bitangent)) <= epsilon
        )
    
class RayHit():
    def __init__(self, hit: bool, hit_point: Vector | None, distance: float=float('inf')):
        self.hit = hit
        self.hit_point = hit_point
        # 0-inf
        self.distance = distance
        self.owner: AttachmentPoint | None = None

    def __repr__(self):
        return f"hit: {self.hit} hit_point: {self.hit_point}"

class Cube():

    def __init__(self):
        self.pos = Vector()
        self.scale = Vector(1, 1, 1)
        self.rot = Vector()

        self.attachment_points = []
        self.attached_objects = []

    def add_attachment_point(self, pos: Vector, direction: Vector, tangent: Vector, normal: Vector, size2D: Vector):
        # bitangent can be calculated
        self.attachment_points.append(AttachmentPoint(pos, direction * size2D.x, tangent * size2D.y, normal))

    def raycast(self, ray_direction: Vector, ray_origin: Vector) -> list[RayHit]:
        ray_hits: list[RayHit] = []
        for attached_object in self.attached_objects:
            ray_hits.extend(attached_object.raycast(ray_direction, ray_origin))
        for attachment_point in self.attachment_points:
            if attachment_point.is_attached:
                continue
            ray_hit = attachment_point.raycast(ray_direction, ray_origin)
            if ray_hit.hit:
                ray_hit.owner = attachment_point
                ray_hits.append(ray_hit)
        return ray_hits

    @property
    def x(self) -> float:
        return self.pos.x

    @property
    def y(self) -> float:
        return self.pos.y

    @property
    def z(self) -> float:
        return self.pos.z

def main():
    """
    x = right left
    y = up down
    z = front back
    """
    base = Cube()

    att_pos = Vector(base.x + (base.scale.x / 2.0), base.y + (base.scale.y / 2.0), base.z + (base.scale.z / 2.0))
    att_dir = Vector(1, 0, 0)
    att_normal = Vector(0, 0, 1)
    att_tangent = Vector(0, 1, 0)

    size2D = Vector(2, 4)
    base.add_attachment_point(att_pos, att_dir, att_tangent, att_normal, size2D)

    new_piece = Cube()
    new_att_pos = Vector(att_pos.x, att_pos.y, -att_pos.z)
    new_piece.add_attachment_point(new_att_pos, att_dir, att_tangent, -att_normal, size2D)

    print(base.attachment_points[0])
    print(new_piece.attachment_points[0])

    # first check for attachment points that match to reduce scope
    ray_from_camera = Vector()
    camera_position = Vector()
    test_hits_from_target_ray = base.raycast(Vector(0, 0, 1), Vector(1, 1, -10))
    test_miss_from_target_ray = base.raycast(Vector(0, 0, 1), Vector(3, 1, -10))
    test_parallel_ray_hits = base.raycast(Vector(1, 0, 0), Vector(1, 1, 0))


    # preprocess with alignment
    attachment_pairs: list[tuple[RayHit, AttachmentPoint]] = []
    for ray_hit in test_hits_from_target_ray:
        for attachment in new_piece.attachment_points:
            # opposites attract
            if ray_hit.owner and ray_hit.owner.normal == -attachment.normal:
                attachment_pairs.append((ray_hit, attachment))
    if len(attachment_pairs) == 0:
        print(f'no hit')
        return
    # might be t need to check
    attachment_pairs.sort(key=lambda pair: pair[0].distance)

    best_hit = attachment_pairs[0]
    best_hit_ray, best_hit_attachment = best_hit

    # TODO: massage so it fit the grid size
    position = best_hit_ray.hit_point
    # REVIEW: `assert` can be stripped with `python -O`; use an explicit runtime check if this is required for correctness.
    assert position is not None
    # TOOD: plus or minus?
    new_piece.pos = position + best_hit_attachment.pos
    # REVIEW: `assert` can be stripped with `python -O`; use an explicit runtime check if this is required for correctness.
    assert best_hit_ray.owner is not None
    best_hit_ray.owner.is_attached = True
    best_hit_attachment.is_attached = True
    base.attached_objects.append(new_piece)

    print(best_hit)
    
    print(test_hits_from_target_ray)
    print(test_miss_from_target_ray)
    print(test_parallel_ray_hits)

    """
    TODO: do raycast between camera and base + all attachments
    maybe get all hits and if there are many return the one that has the lowest t
    then check if there is an attachment that has normal = -normal of an attachment on your new piece
    also need to check what is the optimal attachment on my piece, probably just what fits with the best attachment point that was hit
    add rotation support (doesnt really matter it should be free in real implementation)
    """



if __name__ == "__main__":
    main()