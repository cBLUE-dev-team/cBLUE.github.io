function [ SF] = Cos2S_spread(angle,spread_param)
%Cos2S_spread Cosine2S spreading function for wave generation.
%  Input to the system is the angular distributions
% The angle range could be between -pi/2 to pi/2 or
% -pi to pi. If -pi to pi is chosen, make sure to change the formula to
% angle to angle/2 

Cs=1/(2*sqrt(pi))*gamma(spread_param+1)/gamma(spread_param+0.5);
% Cs=2^(2*spread_param-1)/pi*gamma(spread_param+1)^2/gamma(spread_param+0.5);
SF=Cs.*cos(angle).^(2*spread_param); % This will be angle/2 is angle was defined as -pi to pi.

end

