function [pos, ray_x_pos, ray_y_pos] = GenerateLidarRays(algConst)
% FUNCTION LocateLidarRays:
%
%   [pos, ray_x_pos, ray_y_pos] = GenerateLidarRays(algConst)
%
% This computes, from the algorithm constants in _algConst_, the location
% of the lidar shot point in 3D, and the locations of the simulation rays
% within the lidar beam on the surface of the water.
 
Rypr = TateBryan(deg2rad(algConst.PosAtt.roll), ...
                 deg2rad(algConst.PosAtt.pitch), ...
                 deg2rad(algConst.PosAtt.yaw)); % Laser position w.r.t IMU. The yaw-pitch and roll angle of the IMU. 
pos = algConst.PosAtt.laser_location + Rypr*algConst.Lidar.PG; % Position of the laser with respect to the SBET and IMU coordinates. 
diam = algConst.PosAtt.laser_location(3)*(tand(algConst.Lidar.scan_angle + algConst.Lidar.beam_div/2) - ...
                                          tand(algConst.Lidar.scan_angle - algConst.Lidar.beam_div/2));  % laser beam footprint diameter

% The following represents the laser ray distribution within the laser beam
% footprint.

% Create random points in a circle and superimpose them on the waves. 
% (https://www.mathworks.com/matlabcentral/answers/72915-creating-random-points-in-a-circle)
% First define parameters that define the number of points and the circle.
R = diam/2; % radius of the circle. Here, calculate the laser beam footprint.. 
x0 = algConst.PosAtt.laser_location(3)*tand(algConst.Lidar.scan_angle); % Center of the circle in the x direction.
y0 = 0; % Center of the circle in the y direction.

% Now create the set of points.
t = 2*pi*rand(algConst.Sim.Nrays, 1);
rr = R*sqrt(rand(algConst.Sim.Nrays, 1));
ray_x_pos = x0 + rr.*cos(t);
ray_y_pos = y0 + rr.*sin(t);

end
