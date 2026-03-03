type Vector = Vector
type RayHit = RayHit

class Vector():
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self):
        return f"x:{self.x} y:{self.y} z:{self.z}"
    
    def __mul__(self, other: float) -> Vector:
        return Vector(self.x * other, self.y * other, self.z * other)
    
    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector) -> Vector:
        return self + -other
    
    def __neg__(self):
        return self * -1
    
    def dot(self, other: Vector) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

class AttachmentPoint():
    def __init__(self, pos, bitangent, tangent, normal):
        # corner of plane
        self.pos = pos
        self.bitangent = bitangent
        self.tangent = tangent
        self.normal = normal

    def __repr__(self):
        return f"pos({self.pos}) dir({self.bitangent}) tan({self.tangent}) norm({self.normal})"
    
    def raycast(self, ray_dir: Vector, ray_orig: Vector) -> RayHit:
        ray_hit = RayHit(False, None)
        epsilon = 1e-6

        denom = self.normal.dot(ray_dir)
        # Paralell check
        if abs(denom) < epsilon:
            return ray_hit

        t = self.normal.dot(self.pos - ray_orig) / denom
        if t < 0:  # behind origin
            return ray_hit
        
        hit = ray_orig + (ray_dir * t)

        rel = hit - self.pos

        tangent_dot = self.tangent.dot(self.tangent)
        bitangent_dot = self.bitangent.dot(self.bitangent)
        if tangent_dot < epsilon or bitangent_dot < epsilon:
            return ray_hit
        
        u = rel.dot(self.bitangent) / bitangent_dot
        v = rel.dot(self.tangent) / tangent_dot

        if 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0:
            ray_hit.hit = True
            ray_hit.hit_point = hit
        return ray_hit

    def validate(self):
        return self.bitangent.dot(self.tangent) == 90
    
class RayHit():
    def __init__(self, hit: bool, hit_point: Vector | None):
        self.hit = hit
        self.hit_point = hit_point

    def __repr__(self):
        return f"hit: {self.hit} hit_point: {self.hit_point}"

class Cube():

    def __init__(self):
        self.pos = Vector()
        self.scale = Vector(1, 1, 1)
        self.rot = Vector()

        self.attachment_points = []
        self.attachments = []

    def add_attachment_point(self, pos, dir, tangent, normal, size2D):
        # bitangent can be calculated
        self.attachment_points.append(AttachmentPoint(pos, dir * size2D.x, tangent * size2D.y, normal))

    def raycast(self, ray_dir: Vector, ray_orig: Vector) -> RayHit:
        for attachment_point in self.attachment_points:
            ray_hit = attachment_point.raycast(ray_dir, ray_orig)
            return ray_hit
        return RayHit(False, None)

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

    ray_hit = base.raycast(Vector(0, 0, 1), Vector(1, 1, -10))
    ray_miss = base.raycast(Vector(0, 0, 1), Vector(3, 1, -10))
    ray_parallel = base.raycast(Vector(1, 0, 0), Vector(1, 1, 0))
    print(ray_hit)
    print(ray_miss)
    print(ray_parallel)

    """
    TODO: do raycast between camera and base + all attachments 
    add t
    maybe get all hits and if there are many return the one that has the lowest t
    then check if there is an attachment that has normal = -normal of an attachment on your new piece
    also need to check what is the optimal attachment on my piece, probably just what fits with the best attachment point that was hit

    add rotation support (doesnt really matter it should be free in real implementation) 
    """



main()