import numpy as np


# Rotation matrix which rotates an intial vector v about an axis at an angle theta
# The axis is defined by the crossproduct between the vector v and vector 1,0,0
# If v and 1,0,0 are linear dependent, then axis is defined by crossproduct between v and 0,1,0
def rotation_matrix(v, theta, normalize=False):
    if normalize:
        v_normalized = v / np.linalg.norm(v)
    else:
        v_normalized = v
    axis = np.cross(v_normalized, [1, 0, 0])
    if np.allclose(axis, [0, 0, 0]):
        axis = np.cross(v_normalized, [0, 1, 0])

    angle = np.deg2rad(theta)
    cos_theta = np.cos(angle)
    sin_theta = np.sin(angle)
    ux, uy, uz = axis
    rotation_matrix = np.array([
        [cos_theta + ux**2 * (1 - cos_theta), ux*uy*(1 - cos_theta) - uz*sin_theta,
         ux*uz*(1 - cos_theta) + uy*sin_theta],
        [uy*ux*(1 - cos_theta) + uz*sin_theta, cos_theta + uy**2*(1 - cos_theta),
         uy*uz*(1 - cos_theta) - ux*sin_theta],
        [uz*ux*(1 - cos_theta) - uy*sin_theta, uz*uy*(1 - cos_theta) + ux*sin_theta,
         cos_theta + uz**2*(1 - cos_theta)]
    ])

    return rotation_matrix


def transform(v, theta, normalize=False):
    v_anti = np.dot(rotation_matrix(v, theta, normalize), v)
    if normalize:
        return v_anti / np.linalg.norm(v_anti)
    return v_anti


if __name__ == "__main__":
    # Example case
    # Initial random Stokes vector (not normalized)
    S = np.array([1, 1, 1, 1])
    # Initial stokes vector v neglecting S0
    v = S[1:]
    # v normalized
    v_normalized = v / np.linalg.norm(v)
    print("Initial vector normalized", v_normalized)

    # Construct rotation matrix to rotate vector to the corresponding orthogonal vector
    R = rotation_matrix(v, 180)

    # Antipodal vector/ Orthogonal vector
    v_antipodal = np.dot(R, v)
    print("Antipodal vector", v_antipodal)
    print("Antipodal vector normalized", v_antipodal / np.linalg.norm(v_antipodal))

    # Calculate rotated vectors
    num_steps = 7
    rotated_vectors = []

    angle_values = np.linspace(0, 180, num_steps)

    for i in angle_values:
        v_rotated = transform(v, i, normalize=True)
        # v_rotated /= np.linalg.norm(v_rotated)
        rotated_vectors.append(v_rotated)
    print(rotated_vectors)
