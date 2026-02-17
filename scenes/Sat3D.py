from manim import *


def cylinder_between_points(p1, p2, radius=0.05, color=None):
    # draw russ for meshes, each connection goes from a point
    # at the mesh to a point at the net
    axis = p2 - p1
    height = np.linalg.norm(axis)
    if height == 0:
        return None  # points coincide

    # Unit vector along axis
    axis_normalized = axis / height
    # Default cylinder is along UP (z-axis)
    default_axis = np.array([0, 0, 1])

    # Compute rotation axis and angle
    rot_axis = np.cross(default_axis, axis_normalized)
    rot_axis_norm = np.linalg.norm(rot_axis)

    if rot_axis_norm < 1e-6:
        rot_axis = UP
        rot_angle = 0
    else:
        rot_axis = rot_axis / rot_axis_norm
        rot_angle = np.arccos(np.clip(np.dot(default_axis, axis_normalized), -1, 1))

    # Create cylinder along z-axis
    cyl = Cylinder(radius=radius, height=height, color=color)
    cyl.move_to((p1 + p2) / 2)  # move to midpoint
    if rot_angle != 0:
        cyl.rotate(rot_angle, axis=rot_axis, about_point=(p1 + p2) / 2)

    return cyl


class Sat3DScene(ThreeDScene):
    def create_scalloped_cap(
        self,
        radius=20.0,
        height=2.0,
        num_scallops=6,
        scallop_depth=1,
        mesh_res=[40, 40],
    ):
        """
        Spherical cap with scalloped cutouts carved from the bottom,
        while preserving a perfect spherical surface.
        """

        # Fixed cap angle
        base_z_min = radius - height
        phi_cap = np.arccos(base_z_min / radius)

        def scalloped_phi_cut(v):
            angle_step = TAU / num_scallops
            t = ((v + angle_step / 2) % angle_step) / angle_step

            # triangular wave → sharp peaks
            sharp = abs(np.sin(t * TAU))

            z_cut = base_z_min + scallop_depth * sharp
            return np.arccos(z_cut / radius)

        def rim_point(v):
            # 3D point at u=1 for a given angle v
            phi = scalloped_phi_cut(v)
            return radius * np.array(
                [np.sin(phi) * np.cos(v), np.sin(phi) * np.sin(v), np.cos(phi)]
            )

        cap = Surface(
            lambda u, v: (
                radius
                * np.array(
                    [
                        np.sin(min(u * phi_cap, scalloped_phi_cut(v))) * np.cos(v),
                        np.sin(min(u * phi_cap, scalloped_phi_cut(v))) * np.sin(v),
                        np.cos(min(u * phi_cap, scalloped_phi_cut(v))),
                    ]
                )
            ),
            u_range=[0, 1],
            v_range=[0, TAU],
            resolution=(
                mesh_res[0],
                num_scallops * 10,
            ),
        )

        return cap, rim_point

    def construct(self):

        # Create the mesh and net
        height = 0.5
        num_scallops = 6
        cap1, rim1 = self.create_scalloped_cap(
            radius=15.0, height=height, num_scallops=num_scallops, scallop_depth=0.1
        )
        cap2, _ = self.create_scalloped_cap(
            radius=15.0, height=height, num_scallops=num_scallops, scallop_depth=0.1
        )

        # style mesh reflector
        cap1.set_fill(GOLD_D, opacity=0.9)
        cap1.set_stroke(GOLD_E, width=1.5)
        # style net
        cap2.set_fill(GOLD_E, opacity=0)
        cap2.set_stroke(GOLD_E, width=1, opacity=0.2)

        # flip net and place it slightly above cap1
        cap2.rotate(PI, axis=UP)
        shift_mesh = 14
        shift_net = 13
        cap1.shift(IN * shift_mesh)
        cap2.shift(IN * shift_net)

        # cylinders that connect the mesh and net
        def cylinder_between(p1, p2, radius=0.1, color=BLUE):
            axis = p2 - p1
            height = np.linalg.norm(axis)
            direction = axis / height

            cyl = Cylinder(
                radius=radius, height=height, direction=direction, color=color
            )

            cyl.move_to((p1 + p2) / 2)
            return cyl

        # Loop over each scallop
        for i in range(num_scallops * 2):
            # angle at start of scallop
            v = i * TAU / num_scallops / 2

            # rim point in local cap coordinates
            p_local1 = rim1(v)

            # convert to world coordinates if cap1 has been shifted
            p_world1 = p_local1
            p_world2 = p_local1

            # create a small dot at that position
            dot1 = Dot(p_world1, radius=0.2, color=RED).shift(IN * shift_mesh)
            dot2 = Dot(p_world2, radius=0.2, color=RED).shift(
                IN * shift_net + (height * 1) * OUT
            )
            cyl = cylinder_between(
                dot1.get_center(), dot2.get_center(), radius=0.03, color=BLACK
            ).set_stroke(BLACK)

            self.add(cyl)
        self.add(cap1, cap2)

        # Create solar array: 2x3 grid of rectangles (2 rows, 3 columns)
        rows = 3
        cols = 2
        rect_width = 2
        rect_height = 1
        horizontal_buffer = 0.7
        vertical_buffer = 0.07
        rectangles = VGroup()
        for row in range(rows):
            for col in range(cols):
                # Create a 3D rectangular prism (box)
                rect = Prism(
                    dimensions=[rect_width, rect_height, 0.05]  # width, height, depth
                )

                # Position the rectangle in the grid
                x_pos = (
                    col * (rect_width + horizontal_buffer)
                    - (cols - 1) * (rect_width + horizontal_buffer) / 2
                )
                y_pos = -row * (rect_height + vertical_buffer)

                # Move to position, orthogonal to z-axis (facing OUT)
                rect.move_to([x_pos, y_pos, 0])
                rect.z_index = 1
                rect.set_color(GREY_E).set_fill(
                    opacity=1
                )  # .set_sheen(0.8, direction=UR).set_sheen_color(BLUE_B)
                rectangles.add(rect.shift(2 * OUT + 5 * UP))

        self.add(*rectangles)

        # Create box touching bottom of middle 2 rectangles (columns 1 and 2, row 1)
        # Calculate position of middle 2 rectangles in bottom row
        col1_x = (
            0 * (rect_width + horizontal_buffer)
            - (cols - 1) * (rect_width + horizontal_buffer) / 2
        )
        col2_x = (
            1 * (rect_width + horizontal_buffer)
            - (cols - 1) * (rect_width + horizontal_buffer) / 2
        )
        bottom_row_y = -1 * (rect_height + vertical_buffer)

        # Box spans across both middle rectangles
        box_width = 1.3  # ((col2_x - col1_x) + rect_width)/2
        box_height = 0.75  # Adjust as needed
        box_depth = 1.75
        box = Prism(dimensions=[box_width, box_height, box_depth]).set_fill(
            GREY_E, opacity=1
        )
        box.z_index = 0
        # Position box centered between the two rectangles, touching their bottom
        center_x = (col1_x + col2_x) / 2
        box_y = (
            bottom_row_y - rect_height / 2 - box_height / 2
        )  # Bottom of rectangles minus half box height
        box.move_to([center_x, box_y, 0])
        self.add(box.shift(1.02 * OUT + 6 * UP))

        # First cylinder for horn
        cylinder_radius = 0.07  # Adjust as needed
        cylinder_height = 3.5  # How far along IN direction it extends
        cylinder = Cylinder(radius=cylinder_radius, height=cylinder_height)
        cylinder_z = 1.05 - box_depth / 2 - cylinder_height / 2
        cylinder.move_to([center_x, box_y, cylinder_z])
        cylinder.shift(6 * UP)  # Only apply the UP shift, Z position already set
        cylinder.set_color(GREY_D)
        self.add(cylinder)

        # Second cylinder for horn
        cylinder2_radius = 0.07  # Same as first cylinder
        cylinder2_height = 1  # Length of angled cylinder
        cylinder2 = Cylinder(radius=cylinder2_radius, height=cylinder2_height)
        angle = -PI / 2.75
        cylinder2.rotate(angle, axis=RIGHT)
        # position cylinder
        direction = np.array([0, np.sin(angle), -np.cos(angle)])
        connection_point = cylinder.get_center() + (cylinder_height / 2) * IN
        cylinder2.move_to(connection_point + (cylinder2_height / 2) * direction)
        cylinder2.set_color(GREY_D)
        self.add(cylinder2)

        # feed array box at bottom of second cylinder
        box2_width = 0.5
        box2_height = 0.3
        box2_depth = 0.3
        box2 = Prism(dimensions=[box2_width, box2_height, box2_depth])
        box2_position = cylinder2.get_center() + (cylinder2_height / 2) * direction
        box2.move_to(box2_position)
        box2.set_color(GREY_E)
        box2.z_index = 2
        self.add(box2)

        self.set_camera_orientation(phi=75 * DEGREES, theta=0 * DEGREES, zoom=0.5)
        self.begin_ambient_camera_rotation(rate=0.4)
        self.wait(5)
