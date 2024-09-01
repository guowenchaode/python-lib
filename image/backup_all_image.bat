chcp 65001

set phone_source=%1

@REM call move_to_image_base_dir %phone_source%:\内部存储\DCIM\Camera-bak X:\WD-BACKUP\Image %phone_source%:\内部存储\DCIM\Camera-bak
call move_to_image_base_dir %phone_source%:\内部存储\DCIM\Camera X:\WD-BACKUP\Image %phone_source%:\内部存储\DCIM\Camera-bak