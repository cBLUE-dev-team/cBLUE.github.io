% Monte Carlo simulation program for topo-bathy lidar TPU modeling
% In this version, quaternions (rather than Euler angles) and multiple
% water surface facets are used. 
% Firat Eren 07/07/2017

close all
clc
clearvars -except elev fn
tic

% load surf_normals % Surface normals derived from the Riegl data set.
% In surf_normals.mat file there are two variables.
% 1) fn---> surface normals for the Riegl derived water surface.
% 2) elev--> water surface elevation in ellipsoidal height.
load rays_1000
%-------------------------------------------------------------------------
% User modifiable paramters
%
% Some of these parameters are passed to the core simulation function, and
% therefore need to be gathered together into a structure that can be
% passed more readily.  In order to avoid special cases, they are all
% collected in sub-structures.
%-------------------------------------------------------------------------

% Properties of the simulation.

AlgConst.Sim.Nrays=1000;                 % number of rays used in the MC simulations
AlgConst.Sim.MaxScatterEvents = 20;      % Maximum number of refraction layers to consider
AlgConst.Sim.Nsim=100;                  % Number of MC simulations
AlgConst.Sim.wind_spread =  1:1:10;       % Wind speeds to simulate, in knots
AlgConst.Sim.Kd_spread = 0.06:0.01:0.36; % Absorption coefficient range to simulate (unitless)

% Scatter parameters: probability (albedo), and phase function
AlgConst.Scatter.wo=0.80;       % single scattering albedo
AlgConst.Scatter.g_pf=0.995;	% Henyey-Greenstein phase function forward scattering parameter

% Properties of the environment: refractions, wave height, area depth
AlgConst.Env.air_refraction_index = 1;      % index of refraction in air
AlgConst.Env.water_refraction_index = 1.33; % index of refraction in water 
AlgConst.Env.dshallow = -1;                 % Shallowest depth
AlgConst.Env.ddeep = -10;                    % Deepest depth
AlgConst.Env.water_elevation = 0;           % Water surface elevation (metres)
AlgConst.Env.wave_age = 0.84;                % wave age used in the ECKV modeled water surface
AlgConst.Env.s=6;                           % Spreading function parameter

% Properties of the lidar doing the survey
AlgConst.Lidar.scan_angle=20;  % scanning angle of Riegl VQ-880-G (degrees)
AlgConst.Lidar.beam_div=1;     % half beam divergence angle in mrad. Between 0.7-2 mrad as defined in Riegl Vq-880G document
                               %(http://www.riegl.com/uploads/tx_pxpriegldownloads/DataSheet_VQ-880-G_2016-09-16.pdf).
AlgConst.Lidar.PG = [0; 0; 0]; % This is the distance vector from the airplane rotation sensor, i.e. IMU. to the laser unit (level arm offset vector).
AlgConst.Lidar.dkap = 0;       % Sensor boresight angle (degrees)
AlgConst.Lidar.dpsi = 0;       % Sensor boresight angle (degrees)
AlgConst.Lidar.domeg = 0;      % Sensor boresight angle (degrees)

% Current attitude and position of sensor during simulation
AlgConst.PosAtt.laser_location = [0; 0; 600];   % Laser location (x, y, z) (metres)
AlgConst.PosAtt.roll = 0;                       % Current sensor roll during simulation (degrees)
AlgConst.PosAtt.pitch = 0;                      % Current sensor pitch during simulation (degrees)
AlgConst.PosAtt.yaw = 0;                        % Current sensor yaw during simulation (degrees) 

%-------------------------------------------------------------------------
% Preliminary computations
%
%-------------------------------------------------------------------------
        
% Intermediate computations on the constants to get them into the right
% form for the rest of the computation
AlgConst.Scatter.hg_const_1 = (1 + AlgConst.Scatter.g_pf^2)/(2*AlgConst.Scatter.g_pf);    % Pre-computes part of the scattering computation
AlgConst.Scatter.hg_const_2 = -(1 - AlgConst.Scatter.g_pf^2)/(2*AlgConst.Scatter.g_pf);   % Pre-computes part of the scattering computation

AlgConst.Sim.drange = AlgConst.Env.ddeep:1:AlgConst.Env.dshallow; % Depth range to be simulated
AlgConst.Lidar.beam_div = AlgConst.Lidar.beam_div*0.0572958;        % conversion from mrad to degrees

% We pre-generate a set of AlgConst.Sim.Nrays pseudo-rays within the beam
% divergence in order to Monte Carlo trace them into the water, and work
% out how much they're being shifted by the surface interaction and
% scattering.  The rays are generated in a circle on the water surface
% according to the divergence.
% [POS_LAS1, x_rays1, y_rays1] = GenerateLidarRays(AlgConst);
POS_RAYS=[x_rays,y_rays];
POS_LAS=[0;0;600];
ray1=POS_RAYS(1,:);
%-------------------------------------------------------------------------
% Output space pre-allocation
%
%-------------------------------------------------------------------------

% The mean/std. dev. values being generated in the depth loop (i.e., the
% outputs that we're going to memoise in the LUT) are cached temporarily as
% the depth loop is computed.  The same number of depth points are done on
% each pass, so we can do a one-time allocation here
num_depths = length(AlgConst.Sim.drange);
mean_depth(num_depths, 1) = 0;
std_depth(num_depths, 1) = 0;
mean_x(num_depths, 1) = 0;
std_x(num_depths, 1) = 0;
mean_y(num_depths, 1) = 0;
std_y(num_depths, 1) = 0;
sim_result = zeros(AlgConst.Sim.Nsim, 3);
closest=zeros(AlgConst.Sim.Nrays,3);
index=zeros(AlgConst.Sim.Nrays,1);
%-------------------------------------------------------------------------
% Main simulation loop
%
%-------------------------------------------------------------------------

% The surface wave spectrum depends only on the wave age and wind for the
% most part (i.e., to the scale of the 2D spatial spectrum), so we set-up
% for wave age first, reset to the right wind in the appropriate loop, and
% sample inside the inner-most loop.  This avoids a lot of re-computation
% (and particularly triangulation) in the inner loop.
surface_spectrum = SurfaceSpectrum(AlgConst.Env.wave_age,AlgConst.Env.s);

% For effort tracking, we need to know the total number of inner loops that
% we're going to run, and track the number of depth loops complete (so we
% can estimate the time to finish the total computation).
n_depth_loops = length(AlgConst.Sim.wind_spread)*length(AlgConst.Sim.Kd_spread);
depth_loops_complete = 0;

% The following code generates the index number of surface facets that intersect with the ray
% It will be run once outside the loop. The index values of the water
% surface facet will be used in further simulations. The
% assumption is that we use the same bundle of rays and they always
% intersect at the same location.

surface_spectrum.SetWind(1);
[fn1,center_pt] = surface_spectrum.Sample(0);
center_pt(:,1)=center_pt(:,1)+218.3821; % 218.3821 is the center point of the rays

for i=1:AlgConst.Sim.Nrays
distances = sqrt(sum(bsxfun(@minus, center_pt(:,1:2), POS_RAYS(i,:)).^2,2));
[value, index(i,1)] = min(distances);
% closest(i,:) = center_pt(index(i,1),:);
end
AlgConst.Sim.Index=index;


for wind = AlgConst.Sim.wind_spread
    % The surface spectrum magnitude is only dependent on the wind speed,
    % so we compute here
    surface_spectrum.SetWind(wind);
    
    wind_prefix = ['Wind ', num2str(wind, '%.2f'), ' kt'];
        % For display during the inner (depth) loop
    
    for Kd = AlgConst.Sim.Kd_spread
        cb = (Kd - 0.04)/0.2;  % Conversion from Kd to beam attenuation coefficient
        
        Kd_prefix = ['Kd ', num2str(Kd, '%.2f')];
            % For display during the inner (depth) loop
            
        di = 1; % index variable to output into mean_{depth,x,y} and std_{depth,x,y} as a function of depth loop
        depth_cumulative_time = 0;
        disp(['Generating LUT for ', wind_prefix, ', ', Kd_prefix, '.']);
        for depth = AlgConst.Sim.drange
%             tic
            parfor sim = 1:AlgConst.Sim.Nsim
                sim_result(sim, :)= SimulateShot(depth, cb, POS_LAS, x_rays, y_rays, surface_spectrum, AlgConst);
            end
            
            if AlgConst.Sim.Nsim==1 
            mean_depth=sim_result(3);   
            mean_y=sim_result(2); 
            mean_x=sim_result(1); 
             
            std_depth=0;
            std_y=0;
            std_x=0;
            else
            mean_position = mean(sim_result);
            std_position = std(sim_result);
            
            mean_depth(di) = mean_position(3);
            std_depth(di) = std_position(3);

            mean_x(di) = mean_position(1);
            std_x(di) = std_position(1);
            
            mean_y(di) = mean_position(2);
            std_y(di) = std_position(2);
            end
            elapsed = 1; % normally toc
            depth_cumulative_time = depth_cumulative_time + elapsed;
            depth_mean_time = depth_cumulative_time / di;
            
            di=di+1;

            disp([' ... Computation time for ', wind_prefix, ', ', Kd_prefix, ...
                  ', Depth ', num2str(depth, '%.2f'), 'm: ', ...
                  num2str(elapsed, '%.2f'), 's, mean ', num2str(depth_mean_time, '%.2f'), ...
                  's/depth sample.']);
        end
        
        depth_loops_complete = depth_loops_complete + 1;
        remaining_time = (n_depth_loops - depth_loops_complete)*depth_cumulative_time;
        time_string = FormatTimeString(remaining_time);
        disp([' ... Total time for depth loop ', num2str(depth_cumulative_time, '%.2f'), ...
              's (estimate ', time_string, ' to complete remaining simulations).']);
        
        disp([' ... Saving LUT for ', wind_prefix, ', ', Kd_prefix, '.']);
        LUT=[AlgConst.Sim.drange' mean_x std_x mean_y std_y -mean_depth std_depth];
        save(sprintf('quaternion_table_wind_%d_Kd%.2g_PF%.3g_wave_age%.2g.mat',wind,Kd*100,AlgConst.Scatter.g_pf,AlgConst.Env.wave_age),'LUT')
    end
end
time_pass=toc;
sprintf('MC simulation took %.2f seconds',time_pass)

