function s = FormatTimeString(t)
% FUNCTION FormatTimeString:
%
%   s = FormatTimeString(t)
%
% Convert time _t_ into a printable string, taking into account the
% magnitude (i.e., so < 60 s is printed in seconds, < 1 hr in minutes,
% etc.).

if t < 60
    % Formatting in seconds for times less than a minute
    s = sprintf('%.2f s', t);
else
    if t < 3600
        % Formatting in minutes for times less than an hour
        s = sprintf('%.2f min.', t/60);
    else
        if t < 86400
            % Formatting in hours for times less than a day
            s = sprintf('%.2f hr.', t /3600);
        else
            % Formatting in days for times more than a day
            s = sprintf('%.2f days', t/86400);
        end
    end
end

end
