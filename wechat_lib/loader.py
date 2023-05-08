from wxauto import *
import datetime
import time

# 获取当前微信客户端
wx = WeChat()

# 获取会话列表
wx.GetSessionList()


def ltime(myNumber):
    epoch_start = datetime.datetime(1601, 1, 1)
    delta = datetime.timedelta(microseconds=int(myNumber))
    s = epoch_start + delta

    return s
    # return datetime.datetime(2012, 4, 18, 23, 22, 11, 952304)


###############################
# 1、获取默认窗口聊天信息
###############################
def get_default_window_messages(user, filter, tm=0):
    # 默认是微信窗口当前选中的窗口
    # 输出当前聊天窗口聊天消息
    msgs = wx.GetAllMessage

    process_messages(msgs, user, filter)


    for i in range(tm):
        wx.LoadMoreMessage()
        msgs = wx.GetAllMessage
        process_messages(msgs, user, filter)


def process_messages(msgs, user, filter):
    dt = ''
    for msg in msgs:
        # print('-'*40)
        # print(f'msg=[{msg}]')
        sender, content, l = msg

        if sender == 'Time':
            dt = content.strip()
            continue
        elif user in sender and filter in content:
            print(f'{dt}:\t [{sender}] \n[{content}]')
            print('-'*200)


if __name__ == '__main__':
    print()
    print()
    print()
    get_default_window_messages('陈海燕','表扬榜：')
