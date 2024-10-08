import re
import json
import exifread
import os.path
import time
from datetime import datetime


ISOTIMEFORMAT = '%Y:%m:%d %X'


def latitude_and_longitude_convert_to_decimal_system(*arg):
    """
    经纬度转为小数, param arg:
    :return: 十进制小数
    """
    return float(arg[0]) + ((float(arg[1]) + (float(arg[2].split('/')[0]) / float(arg[2].split('/')[-1]) / 60)) / 60)


def float_to_time(tm):
    dt = time.strftime(ISOTIMEFORMAT, time.localtime(tm))
    return dt


# 读取照片的GPS经纬度信息


def load_image(pic_path):
    GPS = {}
    date = ''
    with open(pic_path, 'rb') as f:
        tags = exifread.process_file(f)
        for tag, value in tags.items():
            # # 纬度
            # if re.match('GPS GPSLatitudeRef', tag):
            #     GPS['GPSLatitudeRef'] = str(value)
            # # 经度
            # elif re.match('GPS GPSLongitudeRef', tag):
            #     GPS['GPSLongitudeRef'] = str(value)
            # # 海拔
            # elif re.match('GPS GPSAltitudeRef', tag):
            #     GPS['GPSAltitudeRef'] = str(value)
            # elif re.match('GPS GPSLatitude', tag):
            #     try:
            #         match_result = re.match(
            #             '\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
            #         GPS['GPSLatitude'] = int(match_result[0]), int(
            #             match_result[1]), int(match_result[2])
            #     except:
            #         deg, min, sec = [x.replace(' ', '')
            #                          for x in str(value)[1:-1].split(',')]
            #         GPS['GPSLatitude'] = latitude_and_longitude_convert_to_decimal_system(
            #             deg, min, sec)
            # elif re.match('GPS GPSLongitude', tag):
            #     try:
            #         match_result = re.match(
            #             '\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
            #         GPS['GPSLongitude'] = int(match_result[0]), int(
            #             match_result[1]), int(match_result[2])
            #     except:
            #         deg, min, sec = [x.replace(' ', '')
            #                          for x in str(value)[1:-1].split(',')]
            #         GPS['GPSLongitude'] = latitude_and_longitude_convert_to_decimal_system(
            #             deg, min, sec)
            # elif re.match('GPS GPSAltitude', tag):
            #     GPS['GPSAltitude'] = str(value)
            if re.match('.*Date.*', tag):
                date = str(value)
                print(f'Image Date:{date}')
        if date == '':
            lt = os.path.getmtime(pic_path)
            date = float_to_time(lt)
            print(f'Image File Date:{date}')
    return {'gps_info': GPS, 'date_info': date}


# 通过baidu Map的API将GPS信息转换成地址
def find_address_from_GPS(GPS):
    """
    使用Geocoding API把经纬度坐标转换为结构化地址。
    :param GPS:
    :return:
    """
    # 调用百度API的ak值，这个可以注册一个百度开发者获得
    secret_key = 'zbLsuDDL4CS2U0M4KezOZZbGUY9iWtVf'
    if not GPS['GPS_information']:
        return '该照片无GPS信息'
    lat, lng = GPS['GPS_information']['GPSLatitude'], GPS['GPS_information']['GPSLongitude']
    baidu_map_api = "http://api.map.baidu.com/geocoder/v2/?ak={0}&callback=renderReverse&location={1},{2}s&output=json&pois=0".format(
        secret_key, lat, lng)
    response = requests.get(baidu_map_api)
    content = response.text.replace("renderReverse&&renderReverse(", "")[:-1]
    print(content)
    baidu_map_address = json.loads(content)
    formatted_address = baidu_map_address["result"]["formatted_address"]
    province = baidu_map_address["result"]["addressComponent"]["province"]
    city = baidu_map_address["result"]["addressComponent"]["city"]
    district = baidu_map_address["result"]["addressComponent"]["district"]
    location = baidu_map_address["result"]["sematic_description"]
    return formatted_address, province, city, district, location


if __name__ == '__main__':
    path = r"E:\内部存储\Pictures\WeiXin\mmexport1724946709544.jpg"   # 图片存放路径
    GPS_info = load_image(pic_path=path)
    # address = find_address_from_GPS(GPS=GPS_info)
    print("拍摄时间：" + GPS_info.get("date_information"))
    # print('照片拍摄地址:' + str(address))
