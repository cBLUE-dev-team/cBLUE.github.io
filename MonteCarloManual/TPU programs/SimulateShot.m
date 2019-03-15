function [mean_pos,refr] = SimulateShot(depth, attenuation_coeff, laser_position, ...
                                   x_start_pos, y_start_pos, ...
                                   surface_spectrum, ...
                                   sc)
% FUNCTION SimulateShot:
%
%   [mean_pos] = SimultateShot(depth,               Maximum depth to trace
%                              attenuation_coeff,   Water attenuation constant
%                              laser_position,      (x,y,z) for laser
%                              x_start_pos,         x-positions for all rays on surface
%                              y_start_pos,         y-positions for all rays on surface
%                              surface_spectrum,    Object to generate surface
%                                                   spectrum realisations
%                              sc)                  Constants for the
%                                                   configuration being simulated
%
% Simulate a single shot of the lidar, generating and then tracing the rays
% through the water to the specified _depth_.  This returns the mean position
% of the simulated rays as a 3x1 (x, y, z)' in _mean_pos_.

scattered_ray_length = -(1/attenuation_coeff)*log(rand(sc.Sim.Nrays, sc.Sim.MaxScatterEvents)); % path length for each ray

rays_albedo = rand(sc.Sim.Nrays,1); % random number for single scattering albedo

is_scattered = rays_albedo <= sc.Scatter.wo; % if the random number is lower than wo, it is a scattering event. 
n_rays_scattered = sum(is_scattered);

% This is the azimuth angle that determines the plane of scattering. 
% scat_anglez=2*pi*rand(n_rays_scattered, sc.Sim.MaxScatterEvents); 
% scat_angley=acos(sc.Scatter.hg_const_1 + sc.Scatter.hg_const_2./(1+sc.Scatter.g_pf*(1.0-2.0*rand(n_rays_scattered, sc.Sim.MaxScatterEvents))));
scat_anglez=360*rand(n_rays_scattered, sc.Sim.MaxScatterEvents);
scat_angley=rad2deg(acos(sc.Scatter.hg_const_1 + sc.Scatter.hg_const_2./(1+sc.Scatter.g_pf*(1.0-2.0*rand(n_rays_scattered, sc.Sim.MaxScatterEvents)))));

% Sub-set out the position and scattered ray lengths for
% only those rays that actually undergo scattering
x = x_start_pos(is_scattered,:);
y = y_start_pos(is_scattered,:);
scattered_ray_length = scattered_ray_length(is_scattered,:);

% Face normal vectors from the modeled water surface
fn1 = surface_spectrum.Sample(0);
rand_select1=randi([1 length(fn1)],1,1);
face_norm=fn1(rand_select1,:); % we use one water surface

RES=[x y sc.Env.water_elevation*ones(size(x))]; % This is the on-water vector.

VECT=[repmat(laser_position(1), size(RES,1), 1) - RES(:,1) ...
      repmat(laser_position(2), size(RES,1), 1) - RES(:,2) ...
      repmat(laser_position(3), size(RES,1),1) - RES(:,3)];
uv=VECT./repmat(sqrt(sum(VECT.*VECT, 2)), 1, 3);
face_norm1=face_norm.*ones(size(uv)); % face_norm is initially defined as a single face. Now replicate to match the size of uv. 

c1 = cross(uv, face_norm1, 2);	% cross product works for vectorization
b1 = sqrt(sum(abs(c1).^2, 2));	% This is the norm operation in vectorized form
dd = dot(uv',face_norm1');      % dot product works for vectorization, just need to conjugate
dd = dd'; % conjugated dd

% The following equations are derived from the Stanford paper
% (https://math.stackexchange.com/questions/13261/how-to-get-a-reflection-vector)
% (https://stackoverflow.com/questions/29758545/how-to-find-refraction-vector-from-incoming-vector-and-surface-normal)
% Refraction
Theta_degrees = atan2d(b1,dd); % Incidence angle for N light rays. 
Refract_ang = asind(sqrt((sc.Env.air_refraction_index/sc.Env.water_refraction_index)^2*(1-cosd(Theta_degrees).^2))); % (Bram de Greve 2006 Computer Graphics paper)
refr_vec = (sc.Env.air_refraction_index/sc.Env.water_refraction_index)*uv - ((sc.Env.air_refraction_index/sc.Env.water_refraction_index)*cosd(Theta_degrees) - sqrt(1-sind(Refract_ang).^2) ).*face_norm;
refr_norm = sqrt(sum(abs(refr_vec).^2,2)); % This is the norm operation in vectorized form
refr_vec = refr_vec./refr_norm;


num_rays = size(x, 1);

upd_pos = zeros(sc.Sim.MaxScatterEvents, 3);
xcalc = zeros(num_rays, 1);
ycalc = zeros(num_rays, 1);
zcalc = zeros(num_rays, 1);

ray_scalar = cosd(sc.Lidar.scan_angle/sc.Env.water_refraction_index);
for ray = 1:num_rays % For each ray

    tk = refr_vec(ray,:);
    posf = [x(ray), y(ray), sc.Env.water_elevation];% position on the water surface
    posf_in = posf;
    for scatter_event = 1:sc.Sim.MaxScatterEvents % For each scattering event
        ff = TateBryanPY(scat_angley(ray, scatter_event), scat_anglez(ray, scatter_event));
        tn = tk*ff; % direction vector
        upd_pos(scatter_event,:) = posf - scattered_ray_length(ray, scatter_event)*tn; % position of the laser after each scattering event
        posf = upd_pos(scatter_event,:); % store the updated laser position as posf and use it in the next iteration
        tk=tn; % update the direction vector
        % Geometrical mean solution
        if posf(3) <= depth % When the last scattered location is deeper than the set depth. use the geometrical mean to calculate the laser position.
            dz1 = posf(3) - depth; % difference between actual depth and the last scattered position within the set depth
            if scatter_event > 1
                dz2 = depth - upd_pos(scatter_event - 1, 3); % difference between actual depth and the scattered position that exceeds the set depth
                upd_pos(scatter_event,:) = (posf*dz2 + upd_pos(scatter_event - 1, :)*dz1)./(dz1 + dz2);
                if upd_pos(scatter_event,3)>upd_pos(scatter_event-1,3)
                    upd_pos(scatter_event,3)=upd_pos(scatter_event-1,3);
                   break 
                end
            
            else % in the case of no scattering and the refraction results in deeper than actual depth. 
                dz2 = depth - posf_in(3); 
                upd_pos(scatter_event,:) = (posf*dz2 + posf_in*dz1)./(dz1 + dz2);
            end 

            % The following lists the laser locations of each scattered
            % event in descending depth values.
            
%             upd_pos1 = [posf_in; upd_pos(1:scatter_event, :)]; % This places the surface values on the 1st row of the element.
%             upd_pos2 = [upd_pos1(end,:); upd_pos1(1:(end-1), :)];
%             upd = upd_pos1 - upd_pos2;
%             r1 = sum(sqrt(sum(upd(2:end,:).^2, 2)));
%             xcalc(ray) = upd_pos1(end, 1);
%             ycalc(ray) = upd_pos1(end, 2);

%             r1 = sum(sqrt(sum((upd_pos(2:end, :) - upd_pos(1:(end-1),:)).^2, 2))) ...
%                  + sqrt(sum((upd_pos(1,:) - posf_in).^2, 2));
%             xcalc(ray) = upd_pos(end, 1);
%             ycalc(ray) = upd_pos(end, 2);
            r1 = sum(sqrt(sum((upd_pos(2:scatter_event, :) - upd_pos(1:(scatter_event-1),:)).^2, 2))) ...
                 + sqrt(sum((upd_pos(1,:) - posf_in).^2, 2));       
%              ray
            xcalc(ray) = upd_pos(scatter_event, 1);
            ycalc(ray) = upd_pos(scatter_event, 2);
            zcalc(ray) = r1*ray_scalar;
            break 
        end
    end
end
% 'frt'
xcalc=xcalc(xcalc~=0);
ycalc=ycalc(ycalc~=0);
zcalc=zcalc(zcalc~=0);
mean_pos = mean([xcalc ycalc zcalc]);
% std_post=std([xcalc ycalc]);
refr=mean((abs(depth)/cosd(15))*refr_vec);
end