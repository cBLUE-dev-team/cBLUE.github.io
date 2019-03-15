function mean_pos = SimulateShot(depth, attenuation_coeff, laser_position, ...
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
n_rays_scattered = sum(is_scattered); % number of rays scattered


% This is the azimuth angle that determines the plane of scattering. 
scat_anglezq=2*pi*rand(n_rays_scattered, sc.Sim.MaxScatterEvents); 
scat_angleyq=acos(sc.Scatter.hg_const_1 + sc.Scatter.hg_const_2./(1+sc.Scatter.g_pf*(1.0-2.0*rand(n_rays_scattered, sc.Sim.MaxScatterEvents))));
% scat_anglez=360*rand(n_rays_scattered, sc.Sim.MaxScatterEvents);
% scat_angley=rad2deg(acos(sc.Scatter.hg_const_1 + sc.Scatter.hg_const_2./(1+sc.Scatter.g_pf*(1.0-2.0*rand(n_rays_scattered, sc.Sim.MaxScatterEvents)))));
% scat_anglez=rad2deg(scat_anglezq);
% scat_angley=rad2deg(scat_angleyq);

% Sub-set out the position and scattered ray lengths for
% only those rays that actually undergo scattering
x = x_start_pos(is_scattered,:);
y = y_start_pos(is_scattered,:);
scattered_ray_length = scattered_ray_length(is_scattered,:);

% Face normal vectors from the modeled water surface

[fn1,~] = surface_spectrum.Sample(0); % c_point is the center point
face_norm=fn1(sc.Sim.Index,:);
% size(fn1)
face_norm1=face_norm(is_scattered,:);

RES=[x y sc.Env.water_elevation*ones(size(x))]; % This is the on-water vector.

VECT=[repmat(laser_position(1), size(RES,1), 1) - RES(:,1) ...
      repmat(laser_position(2), size(RES,1), 1) - RES(:,2) ...
      repmat(laser_position(3), size(RES,1),1) - RES(:,3)];
uv=VECT./repmat(sqrt(sum(VECT.*VECT, 2)), 1, 3);

% size(uv)
% face_norm1=face_norm.*ones(size(uv)); % face_norm is initially defined as a single face. Now replicate to match the size of uv. 

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
refr_vec = (sc.Env.air_refraction_index/sc.Env.water_refraction_index)*uv - ((sc.Env.air_refraction_index/sc.Env.water_refraction_index)*cosd(Theta_degrees) - sqrt(1-sind(Refract_ang).^2) ).*face_norm1;
refr_norm = sqrt(sum(abs(refr_vec).^2,2)); % This is the norm operation in vectorized form
refr_vec = refr_vec./refr_norm;
% mean(Refract_ang)
num_rays = size(x, 1);

upd_pos = zeros(sc.Sim.MaxScatterEvents, 3);
xcalc = zeros(num_rays, 1);
ycalc = zeros(num_rays, 1);
zcalc = zeros(num_rays, 1);

% Quaternion calculation
q=angle2quat(scat_anglezq,scat_angleyq,zeros(size(scat_angleyq)));
% size(q)

ray_scalar = cosd(sc.Lidar.scan_angle/sc.Env.water_refraction_index);
for ray = 1:num_rays % For each ray (num_rays is the variable)
    tk = refr_vec(ray,:);
    posf = [x(ray), y(ray), sc.Env.water_elevation];% position on the water surface
    posf_in = posf;
%     tic
    for scatter_event = 1:sc.Sim.MaxScatterEvents % For each scattering event
        ind_q=n_rays_scattered*(scatter_event-1)+ray;
        q0=q(ind_q,1);
        q1=q(ind_q,2);
        q2=q(ind_q,3);
        q3=q(ind_q,4);

        q11=1-2*q2^2-2*q3^2;
        q12=2*(q1*q2-q0*q3);
        q13=2*(q1*q3+q0*q2);

        q21=2*(q1*q2+q0*q3);
        q22=1-2*q1^2-2*q3^2;
        q23=2*(q2*q3-q0*q1);

        q31=2*(q1*q3-q0*q2);
        q32=2*(q2*q3+q0*q1);
        q33=1-2*q1^2-2*q2^2;
        ff=[q11,q12,q13;q21,q22,q23;q31,q32,q33];
%         ff = TateBryanPY(scat_angley(ray, scatter_event), scat_anglez(ray, scatter_event));

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
            else % in the case of no scattering and the refraction results in deeper than actual depth. 
                dz2 = depth - posf_in(3); 
                upd_pos(scatter_event,:) = (posf*dz2 + posf_in*dz1)./(dz1 + dz2);
            end 
           
            r1 = sum(sqrt(sum((upd_pos(2:scatter_event, :) - upd_pos(1:(scatter_event-1),:)).^2, 2))) ...
                 + sqrt(sum((upd_pos(1,:) - posf_in).^2, 2));
            xcalc(ray) = upd_pos(scatter_event, 1);
            ycalc(ray) = upd_pos(scatter_event, 2);
            zcalc(ray) = r1*ray_scalar;
            break 
        end
    end
end
xcalc=xcalc(xcalc~=0);
ycalc=ycalc(ycalc~=0);
zcalc=zcalc(zcalc~=0);
mean_pos = mean([xcalc ycalc zcalc]);

end