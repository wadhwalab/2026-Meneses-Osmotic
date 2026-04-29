data_path = uigetdir(pwd,'Select folder containig the files to analyze'); %select the folder wanted
cd(data_path); %set the path

num = 10;
data = strcat(data_path,'\cell_',num2str(num));
cd(data);
Files=dir('*crop.mat');
filename=[Files(1).name(1:5) '.avi'];
A = load(fullfile(data,strcat(filename(1:end-4),'_freq.mat')));
T = A.T;
F = A.F;
F=medfilt1(F,100,'omitnan','truncate'); 

plot(T,-F,'-k');

% Make a time-freq plot for the whole data and save it
%ylim([min([0 min(F)]) 30]) % max expected freq = ~ 20. change this if needed
xlabel('Time [s]')
ylabel('Rotation Frequency [Hz]')
title ('Rotation frequency [Hz] of a single tethered E.Coli cell during 500mM osmotic upshift over time [s]')
xlim([0 400])
ylim([0 100])  
set(gca,'Fontsize',20)

set(gcf,'PaperUnits','centimeters')
xSize = 20; ySize = 10;
%xLeft = 50; yTop = 50 ;
%set(gcf,'PaperPosition',[xLeft yTop xSize ySize])
set(gcf,'Position',[10 20 xSize*100 ySize*100])
pause(0.5)
saveas(gcf,strcat('cell_',num2str(num),'_500_speed_plot'),'fig');
saveas(gcf,strcat('cell_',num2str(num),'_500_speed_plot'),'png');
close(gcf);

end