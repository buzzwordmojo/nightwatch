// KnightWatcher — Andar ADTE210400XXNA + HLK-LD6002 enclosure
// Wall/headboard mount, fixed tilt, radome front.
//
// STATUS: DRAFT — every dimension marked CALIPER below is a placeholder
// estimated from a photo (scaled off the 8.94mm USB-C receptacle and 2.54mm
// header pitch). Replace with real caliper measurements before printing.
//
// Radome physics (60 GHz): the front window prints SOLID (100% infill) at
// radome_thickness ~= a half-wavelength in the plastic, which minimizes
// reflection. PLA/PETG only - never silk, metallic, or carbon-fiber filament
// in front of the antenna. Set radome_open=true for a plain cutout instead;
// print one of each and A/B them with the 5-minute lock test.

/* [Andar carrier board - CALIPER] */
board_length      = 66;    // CALIPER mm, long axis
board_width       = 40;    // CALIPER mm
board_thickness   = 1.6;   // PCB standard
stack_height      = 20;    // CALIPER mm, carrier bottom -> top of LD6002
back_clearance    = 3;     // CALIPER mm, tallest thing below the carrier

/* [USB-C exit - CALIPER] */
usbc_edge_offset  = 20;    // CALIPER mm, connector center from board corner
usbc_cut_w        = 13;    // clearance for plug overmold
usbc_cut_h        = 8;

/* [Mount holes on carrier - CALIPER] */
hole_dia          = 3.2;   // CALIPER mm (M3 standoffs assumed)
hole_inset_x      = 3.5;   // CALIPER mm from board corner
hole_inset_y      = 3.5;   // CALIPER

/* [LD6002 window - CALIPER] */
// The green module's antenna face; window must frame both patch antennas.
module_w          = 35;    // CALIPER mm
module_h          = 35;    // CALIPER mm
module_off_x      = 15;    // CALIPER mm, module corner from carrier corner
module_off_y      = 2;     // CALIPER

/* [Radome] */
radome_open       = false; // true = cutout, false = solid thin window
radome_thickness  = 1.6;   // ~half-wave in PLA/PETG at 60 GHz
radome_standoff   = 2.5;   // air gap to antenna face, ~lambda/2 steps

/* [Case] */
wall              = 2.4;   // 3 perimeters at 0.8
fit_tol           = 0.3;
tilt_angle        = 45;    // headboard aim-down; print variants 30/45/60
mount_hole_dia    = 4;
$fn = 48;

// ---- derived ----
cav_l = board_length + fit_tol*2;
cav_w = board_width  + fit_tol*2;
cav_d = stack_height + back_clearance + radome_standoff;

outer_l = cav_l + wall*2;
outer_w = cav_w + wall*2;
outer_d = cav_d + wall + (radome_open ? wall : radome_thickness);

module standoffs() {
    for (p = [[hole_inset_x, hole_inset_y],
              [board_length - hole_inset_x, hole_inset_y],
              [hole_inset_x, board_width - hole_inset_y],
              [board_length - hole_inset_x, board_width - hole_inset_y]])
        translate([wall + fit_tol + p[0], wall + fit_tol + p[1], wall])
            difference() {
                cylinder(d=hole_dia + 3.2, h=back_clearance);
                cylinder(d=hole_dia - 0.4, h=back_clearance + 1); // self-tap M3
            }
}

module shell() {
    difference() {
        cube([outer_l, outer_w, outer_d]);
        // cavity
        translate([wall, wall, wall])
            cube([cav_l, cav_w, cav_d + 1]);
        // radome window (top face = front, prints face-down for smooth finish)
        win_x = wall + fit_tol + module_off_x - 2;
        win_y = wall + fit_tol + module_off_y - 2;
        translate([win_x, win_y, radome_open
                   ? outer_d - wall - 0.01
                   : outer_d - radome_thickness - (wall - radome_thickness)])
            cube([module_w + 4, module_h + 4,
                  radome_open ? wall + 1 : (wall - radome_thickness) + 0.01]);
        // USB-C exit, bottom edge
        translate([wall + fit_tol + usbc_edge_offset - usbc_cut_w/2, -1,
                   wall + back_clearance + board_thickness - 1])
            cube([usbc_cut_w, wall + 2, usbc_cut_h]);
    }
    standoffs();
}

module wedge() {
    // Separate wall wedge; case screws to it. Rigid, no joints to droop.
    w = outer_w;
    difference() {
        rotate([tilt_angle, 0, 0])
            cube([outer_l, w, 6]);
        // keyhole slots for wall screws
        for (x = [outer_l*0.25, outer_l*0.75])
            translate([x, w*0.5, -10]) cylinder(d=mount_hole_dia, h=40);
    }
}

shell();
translate([0, outer_w + 12, 0]) wedge();
