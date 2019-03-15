function [S,cp,c,cm,am] = ECKV_spectrum(k,U_10,Omega_c)
%UNTITLED3 Pierson-Moskowitz omnidirectional wave spectrum (continuous)
%   Function uses angular spatial frequency, k.

alpha=0.0081;
beta=1.25;
g=9.82;

% k=abs(k);
% Omega_c=3.5; % age of the waves for a given wind speed
%         = 0.84 for a fully developed sea (corresponds to Pierson-Moskowitz)
%         = 1 for a "mature" sea [used in ECKV Fig 8a]
%         = 2 to 5 for a "young" sea; the maximum allowed value is 5
Cd=0.00144; % drag coefficient
u_star=sqrt(Cd)*U_10;

km=370;
cm=0.23; % phase speed of the wave with spatial frequency, km
am=0.13*u_star/cm;
if Omega_c<=1
    gamm=1.7;
else 
    gamm=1.7+6*log10(Omega_c);
end

sigma=0.08*(1+4*(Omega_c^-3));

alpha_p=0.006*Omega_c^0.55; % rear face or Phillips and Kitaigorodskii equilibrium range parameter
if u_star<=cm
alpha_m=0.01*(1+log(u_star/cm));

else
alpha_m=0.01*(1+3*log(u_star/cm))  ;  
end

ko=g/(U_10^2);
kp=ko*(Omega_c)^2 ; % wave number of the of the maximum spectrum (or spectral peak)
cp=sqrt(g/kp) ;% phase speed of the wave with spatial frequency kp

% k=370;
c=sqrt((g./k).*(1+(k/km).^2)); % phase speed of the wave with all frequencies

L_PM=exp(-1.25*(kp./k).^2); % Pierson-Moskowitz shape spectrum
Gam=exp((-1/(2*sigma^2))*(sqrt(abs(k)./kp)-1).^2);
Jp=gamm.^Gam; % Peak enhancement or "overshoot factor" introduced by Hasselmann
Fm=L_PM.*Jp.*exp(-0.25*((k./km)-1).^2);
Fp=L_PM.*Jp.*exp(-0.3162*Omega_c*(sqrt(abs(k)./kp)-1));
Bl=0.5*alpha_p*(cp./c).*Fp;
Bh=0.5*alpha_m*(cm./c).*Fm;
S=(Bl+Bh)./(k.^3); % 1-D omnidirectional wave spectrum



end