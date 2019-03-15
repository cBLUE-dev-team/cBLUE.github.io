function R = TateBryanPY(pitch, yaw)
% FUNCTION TateBryanPY:
%
%   R = TateBryanPY(pitch, yaw)
%
% Compose the reduced rotation matrix, in Tate-Bryan order, for the given
% orientation angles, assuming zero roll

R = [cosd(yaw) -sind(yaw) 0; sind(yaw) cosd(yaw) 0; 0 0 1]*...
    [cosd(pitch) 0 sind(pitch); 0 1 0; -sind(pitch) 0 cosd(pitch)];

end
