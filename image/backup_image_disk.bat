chcp 65001

set source=E
set target=F

@REM WD-BACKUP

@REM call move_to_image_base_dir %source%:\内部存储\DCIM\Camera-bak %target%:\Image %source%:\内部存储\DCIM\Camera-bak-bak
call move_to_image_base_dir %source%:\内部存储\Pictures\WeiXin %target%:\Image %source%:\内部存储\Pictures\WeiXin-bak

@REM call move_to_image_base_dir E:\内部存储\DCIM\Camera %source%:\WD-BACKUP\Image E:\内部存储\DCIM\Camera-bak
