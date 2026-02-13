// Nightwatch Radar Wall Enclosure
// Houses LD2450 radar + CP2102 USB-UART adapter
// Designed for wall mounting with 45° downward tilt

/* [Main Dimensions] */
wall_thickness = 2;          // mm
outer_width = 50;            // mm
outer_height = 70;           // mm
outer_depth = 30;            // mm (at deepest point)
tilt_angle = 45;             // degrees - points radar down

/* [LD2450 Radar] */
radar_width = 24;            // mm
radar_height = 30;           // mm
radar_depth = 8;             // mm
radar_window_margin = 2;     // mm extra around radar

/* [CP2102 USB-UART] */
cp2102_width = 25;           // mm
cp2102_height = 15;          // mm
cp2102_depth = 5;            // mm

/* [Cable/Mounting] */
usb_cable_dia = 8;           // mm (micro USB cable)
usb_exit_dia = 12;           // mm (with strain relief space)
mount_hole_dia = 4;          // mm (for screws)
mount_hole_inset = 8;        // mm from edges

/* [Tolerances] */
fit_tolerance = 0.3;         // mm added to component pockets

/* [Rendering] */
$fn = 32;                    // circle smoothness

// Calculated values
inner_width = outer_width - (wall_thickness * 2);
inner_height = outer_height - (wall_thickness * 2);
inner_depth = outer_depth - wall_thickness;

radar_pocket_w = radar_width + fit_tolerance * 2;
radar_pocket_h = radar_height + fit_tolerance * 2;
radar_pocket_d = radar_depth + fit_tolerance;

cp2102_pocket_w = cp2102_width + fit_tolerance * 2;
cp2102_pocket_h = cp2102_height + fit_tolerance * 2;
cp2102_pocket_d = cp2102_depth + fit_tolerance + 3; // extra for USB port

// Main enclosure module
module enclosure_base() {
    difference() {
        // Outer shell
        cube([outer_width, outer_depth, outer_height]);

        // Inner cavity
        translate([wall_thickness, wall_thickness, wall_thickness])
            cube([inner_width, inner_depth, inner_height + 1]);

        // Radar window (front cutout)
        window_w = radar_width + radar_window_margin * 2;
        window_h = radar_height + radar_window_margin * 2;
        window_z = outer_height - wall_thickness - radar_pocket_h - 5;
        translate([(outer_width - window_w) / 2, -1, window_z])
            cube([window_w, wall_thickness + 2, window_h]);

        // USB cable exit hole (bottom)
        translate([outer_width / 2, outer_depth / 2, -1])
            cylinder(d=usb_exit_dia, h=wall_thickness + 2);

        // Mount holes (keyhole slots)
        // Top hole
        translate([outer_width / 2, outer_depth + 1, outer_height - mount_hole_inset])
            rotate([90, 0, 0])
                mount_keyhole();

        // Bottom hole
        translate([outer_width / 2, outer_depth + 1, mount_hole_inset + 10])
            rotate([90, 0, 0])
                mount_keyhole();

        // Ventilation slots (sides)
        for (z = [15 : 8 : 55]) {
            // Left side
            translate([-1, outer_depth / 2, z])
                cube([wall_thickness + 2, 10, 2]);
            // Right side
            translate([outer_width - wall_thickness - 1, outer_depth / 2, z])
                cube([wall_thickness + 2, 10, 2]);
        }
    }

    // Radar mounting posts
    radar_z = outer_height - wall_thickness - radar_pocket_h - 3;
    post_h = 5;

    // Corner posts to hold radar
    translate([wall_thickness + 2, wall_thickness + 2, radar_z - post_h])
        cylinder(d=3, h=post_h);
    translate([outer_width - wall_thickness - 2, wall_thickness + 2, radar_z - post_h])
        cylinder(d=3, h=post_h);

    // CP2102 mounting shelf
    shelf_z = wall_thickness + 5;
    shelf_depth = cp2102_pocket_d + 2;
    translate([wall_thickness, wall_thickness, shelf_z])
        cube([inner_width, shelf_depth, 2]);
}

// Keyhole mount slot
module mount_keyhole() {
    hull() {
        cylinder(d=mount_hole_dia, h=wall_thickness + 2);
        translate([0, -6, 0])
            cylinder(d=mount_hole_dia * 1.8, h=wall_thickness + 2);
    }
}

// Lid module
module enclosure_lid() {
    lid_thickness = wall_thickness;
    lip_depth = 3;
    lip_tolerance = 0.2;

    difference() {
        union() {
            // Main lid plate
            cube([outer_width, outer_depth, lid_thickness]);

            // Inner lip (fits inside enclosure)
            translate([wall_thickness + lip_tolerance,
                       wall_thickness + lip_tolerance,
                       lid_thickness])
                cube([inner_width - lip_tolerance * 2,
                      inner_depth - lip_tolerance * 2,
                      lip_depth]);
        }

        // Snap fit notches (cut into lip)
        for (x = [outer_width * 0.25, outer_width * 0.75]) {
            translate([x - 2, wall_thickness - 1, lid_thickness])
                cube([4, wall_thickness + 2, lip_depth + 1]);
        }
    }

    // Snap fit bumps on sides
    for (x = [outer_width * 0.25, outer_width * 0.75]) {
        translate([x, wall_thickness + lip_tolerance + 0.5, lid_thickness + lip_depth - 1])
            sphere(d=1.5);
    }
}

// Angled wall mount bracket (optional separate piece)
module wall_bracket() {
    bracket_width = outer_width + 10;
    bracket_height = 20;
    bracket_depth = 15;

    difference() {
        union() {
            // Flat wall plate
            cube([bracket_width, 3, bracket_height + outer_depth * sin(tilt_angle)]);

            // Angled support
            translate([0, 3, 0])
                rotate([tilt_angle, 0, 0])
                    cube([bracket_width, outer_depth + 5, 3]);
        }

        // Screw holes for wall
        translate([bracket_width * 0.2, -1, bracket_height / 2])
            rotate([-90, 0, 0])
                cylinder(d=4, h=5);
        translate([bracket_width * 0.8, -1, bracket_height / 2])
            rotate([-90, 0, 0])
                cylinder(d=4, h=5);
    }
}

// ---- RENDER SELECTION ----
// Uncomment the part you want to render/export

// Main enclosure base
enclosure_base();

// Lid (translate for viewing)
// translate([outer_width + 10, 0, 0]) enclosure_lid();

// Wall bracket (optional)
// translate([0, outer_depth + 20, 0]) wall_bracket();

// All parts for preview
// enclosure_base();
// translate([outer_width + 10, 0, 0]) enclosure_lid();
// translate([0, outer_depth + 20, 0]) wall_bracket();
