classdef SurfaceSpectrum < handle
    properties
        Lx = 20.0   % Length of spatial domain in x (m)
        Ly = 20.0   % Length of spatial domain in y (m)
        Nx = 2^6    % Number of samples in spatial domain in x
        Ny = 2^6    % Number of samples in spatial domain in y
        wave_age    % Non-dimensional wave age parameter for spectrum
        kfx         % Spatial frequencies in x axis
        kfy         % Spatial frequencies in y axis
        k           % Vector of spatial frequency bins for (I)FFT
        SF          % Spectral spreading function (cache)
        g = 9.82    % Gravitational constant (?)
        X           % Grid of sample locations in space (m)
        Y           % Grid of sample locations in space (m)
        domain_triangulation
                    % Delaunay triangulation of the computational domain
        scaled_frequency_bins
                    % Normalised, wrapped frequency, bin numbers in u axis
        wave_spectrum
                    % Spatial spectrum magnitude for wave surface (cached)
    end
    methods
        function obj = SurfaceSpectrum(wave_age,spr)
            % The wave age is only used when the 1D spectrum is generated
            % (in SetWind()), so we just cache this for now.
            obj.wave_age = wave_age;
            
            % Default constructor for the object
            dx = obj.Lx/obj.Nx; % Spatial resolution in x and y-axisw
            dy = obj.Ly/obj.Ny;

            vfx = 1/obj.Lx; % fundamental frequencies of x-axis
            obj.kfx = 2*pi*vfx;

            vfy = 1/obj.Ly; % fundamental frequencies of y-axis
            obj.kfy = 2*pi*vfy;

            NyxL = 2*dx; % minimum wavelength

            VNyx = 1/NyxL;% Nyquist frequency in x-axis
            kNyx = 2*pi*VNyx; % angular Nyquist frequency in x-axis

            r = 0:obj.Nx-1; % index number for x-axis
            s = 0:obj.Ny-1; % index number fot y-axis
            RES(1,1)=0; % These two are added on later
            RES(1,2)=0;
            xr = r*dx + RES(1,1) - obj.Lx/2; % Spatial index- length and width
            ys = s*dy - RES(1,2) - obj.Ly/2; % Depends on the location of the footprint

            u = (-(obj.Nx/2-1):obj.Nx/2);
            v = (-(obj.Ny/2-1):obj.Ny/2);

            % Spatial variables in Math order
            kxu = u*obj.kfx;
            kyv = v*obj.kfy;

            obj.k = 0:obj.kfx:kNyx;
            
            ang=linspace(-pi/2,pi/2,obj.Nx);

%             spr = 6;  % MAGIC NUMBER - REASON UNKNOWN
            obj.SF = Cos2S_spread(ang,spr); % Spreading function
            
            [KX, ~] = meshgrid(kxu,kyv);
            obj.scaled_frequency_bins = sqrt(obj.g*KX);
            [obj.X, obj.Y] = meshgrid(xr,ys);

            obj.domain_triangulation = ...
                delaunayTriangulation(reshape(obj.X,numel(obj.X), 1), ...
                                      reshape(obj.Y,numel(obj.Y), 1)); %find the vertex ID's
                                  
            obj.wave_spectrum = []; % Mark that the spectrum has yet to be generated
        

        end
        function SetWind(obj, wind)
            % Set the current wind conditions (in knots)
            
            [S,~,~,~,~] = ECKV_spectrum(obj.k, wind*0.51444, obj.wave_age); % conversion to m/s
                % Omnidirectional 1D Pierson-Moskowitz wave spectrum
            S(1) = 0;   % Reset mean value (D.C. term) to zero
            obj.wave_spectrum = sqrt(obj.SF'*S*obj.kfx*obj.kfy/2);
        end
        function [face_normals,center_point] = Sample(obj, t)
            % Sample the surface, at time t, returning triangulated face
            % normal vectors for the surface
            
            if isempty(obj.wave_spectrum)
                error('That object does not have a wave spectrum defined.');
            end
            
            % The phase information is generated as a Argand pair of normal
            % deviates, rather than doing a uniform phase and trying to
            % remap to Argand outputs.
            rho = randn(size(obj.wave_spectrum));
            sig = randn(size(obj.wave_spectrum));
            zhat = zeros(size(obj.wave_spectrum));
            
            t_c = sqrt(t);
            cos_f = cos(t_c*obj.scaled_frequency_bins);
            sin_f = sin(t_c*obj.scaled_frequency_bins);
            
            range_row = 2:size(obj.wave_spectrum, 1);
            range_col = 2:size(obj.wave_spectrum, 2);
            zhat(range_row, range_col) = ...
                complex(rho(range_row, range_col).*obj.wave_spectrum(range_row, range_col).*cos_f(range_row, range_col) ...
                        - sig(range_row, range_col).*obj.wave_spectrum(range_row, range_col).*sin_f(range_row, range_col), ...
                        rho(range_row, range_col).*obj.wave_spectrum(range_row, range_col).*sin_f(range_row, range_col) ...
                        + sig(range_row, range_col).*obj.wave_spectrum(range_row, range_col).*cos_f(range_row, range_col));
            
%             for i=2:size(obj.wave_spectrum,1)
%                for j=2:size(obj.wave_spectrum,2)
%                 zhat(i,j) = complex(rho(i,j)*obj.wave_spectrum(i,j)*cos_f(i,j)...
%                             -sig(i,j)*obj.wave_spectrum(i,j)*sin_f(i,j),...
%                             rho(i,j)*obj.wave_spectrum(i,j)*sin_f(i,j)...
%                             +sig(i,j)*obj.wave_spectrum(i,j)*cos_f(i,j));
%                end
%             end

            range_col = 2:size(obj.wave_spectrum, 2);
            z_hat(1, range_col) = complex(rho(1, range_col).*obj.wave_spectrum(1, range_col).*cos_f(1, range_col) ...
                                          - sig(1, range_col).*obj.wave_spectrum(1, range_col).*sin_f(1, range_col), ...
                                          rho(1, range_col).*obj.wave_spectrum(1, range_col).*sin_f(1, range_col) ...
                                          + sig(1, range_col).*obj.wave_spectrum(1, range_col).*cos_f(1, range_col));
                                      
%             for j=2:size(obj.wave_spectrum,2)
%                 zhat(1,j) = complex(rho(1,j)*obj.wave_spectrum(1,j)*cos_f(1,j)...
%                             -sig(1,j)*obj.wave_spectrum(1,j)*sin_f(1,j), ...
%                             rho(1,j)*obj.wave_spectrum(1,j)*sin_f(1,j)...
%                             +sig(1,j)*obj.wave_spectrum(1,j)*cos_f(1,j));
%             end

            range_row = 2:size(obj.wave_spectrum,1)/2+1;
            zhat(range_row, 1) = complex(rho(range_row, 1).*obj.wave_spectrum(range_row, 1).*cos_f(range_row, 1) ...
                                         - sig(range_row, 1).*obj.wave_spectrum(range_row, 1).*sin_f(range_row, 1), ...
                                         rho(range_row, 1).*obj.wave_spectrum(range_row, 1).*sin_f(range_row, 1) ...
                                         + sig(range_row, 1).*obj.wave_spectrum(range_row, 1).*cos_f(range_row, 1));
            
%             for i=2:size(obj.wave_spectrum,1)/2+1
%                 zhat(i,1) = complex(rho(i,1)*obj.wave_spectrum(i,1)*cos_f(i,1)...
%                             -sig(i,1)*obj.wave_spectrum(i,1)*sin_f(i,1), ...
%                             rho(i,1)*obj.wave_spectrum(i,1)*sin_f(i,1)...
%                             +sig(i,1)*obj.wave_spectrum(i,1)*cos_f(i,1));
%             end

            zhat(1,1) = complex(0,0);

            zhat2 = fliplr(conj(zhat)); % Here I flipped the negative frequencies to make it in frequency order
            zhat2(:,1) = [];
            zhat2(:,end) = [];
            zhat2 = flipud(zhat2);
            zhat = [zhat2 zhat];

            zhat_ifft = ifftshift(zhat);
            Z = real(ifft2(zhat_ifft,'symmetric'));

            surf_el = obj.Nx*obj.Ny*Z;
            TR = triangulation(obj.domain_triangulation.ConnectivityList, ...
                               reshape(obj.X,numel(obj.X), 1), ...
                               reshape(obj.Y,numel(obj.Y), 1), ...
                               reshape(surf_el,numel(surf_el), 1));
            face_normals = faceNormal(TR);
            center_point=incenter(TR);
%             TRI=delaunay(obj.X,obj.Y);
            
%             trisurf(TRI,reshape(obj.X,1,size(obj.X,1)*size(obj.X,2))'...
%             ,reshape(obj.Y,1,size(obj.Y,1)*size(obj.Y,2))',reshape(surf_el,1,...
%             size(surf_el,1)*size(surf_el,2))', ...
%             'FaceColor', 'blue', 'faceAlpha', 0.5);
%             zlim([-0.5 0.5])
%        Height=max(max(surf_el))-min(min(surf_el))
        
        
        end
    end
    methods (Access = private)
    end
end
