import requests
from lxml import etree
 
# 确保使用代理或者正确的headers，这里只是示例，实际情况需要你自己处理
headers = {
    'User-Agent': 'your_user_agent',
    # 如果需要可以添加更多headers信息
}
 
# 要抓取的小红书帖子URL
url = 'https://www.xiaohongshu.com/discovery/item/6196945d000000000100244f'
 
# 发送请求
response = requests.get(url, headers=headers)
 
# 解析网页
tree = etree.HTML(response.text)
 
# 提取评论
comments = tree.xpath('//div[@class="comment-item"]')
 
# 打印评论内容
for comment in comments:
    content = comment.xpath('.//span[@class="content"]/text()')[0]
    print(content)