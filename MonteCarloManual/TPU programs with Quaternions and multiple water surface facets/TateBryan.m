function R = TateBryan(roll, pitch, yaw)
% FUNCTION TateBryan:
%
%   R = TateBryan(roll, pitch, yaw)
%
% Compose the total rotation matrix, in Tate-Bryan order, for the given
% orientation angles

R = [cos(yaw) -sin(yaw) 0; sin(yaw) cos(yaw) 0; 0 0 1]*...
    [cos(pitch) 0 sin(pitch); 0 1 0; -sin(pitch) 0 cos(pitch)]*...
    [1 0 0; 0 cos(roll) -sin(roll); 0 sin(roll) cos(roll)];

end
