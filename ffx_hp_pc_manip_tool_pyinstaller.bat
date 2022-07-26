@echo off
set name="FFX HD PC manip tool"
set file_name="%~dp0ffx_hd_pc_manip_tool.py"
pyinstaller --noconfirm --onefile --name=%name% %file_name%
set name="FFX HD PC manip tool - countdown"
set file_name="%~dp0ffx_hd_pc_manip_tool - countdown.py"
pyinstaller --noconfirm --onefile --name=%name% %file_name%
pause
