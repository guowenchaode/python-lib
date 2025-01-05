import requests
from lxml import etree


def get_followees(user_id, max_page=5):
    """获取指定用户的粉丝列表"""
    base_url = f"https://www.xiaohongshu.com/discovery/user/followee/{user_id}?page="

    base_url = r"https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend"
    followees = []
    for page in range(1, max_page + 1):
        url = base_url + str(page)
        response = requests.get(url)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            items = html.xpath('//a[@class="cover ld mask"]')
            for item in items:
                followee = {
                    "name": item.xpath(".//h3/text()")[0],
                    "id": item.xpath(".//@data-id")[0],
                    "avatar": item.xpath(".//img/@src")[0],
                    "intro": item.xpath('.//p[@class="intro"]/text()')[0].strip(),
                }
                followees.append(followee)
        else:
            print(f"Failed to retrieve page: {page}")
            break
    return followees


# 使用示例
user_id = "你的用户ID"  # 替换为你要抓取的粉丝数据对应的用户ID
followees = get_followees(user_id)
for followee in followees:
    print(followee)
