import sys
sys.path.append(r'D:/Git/github/python-lib')
from lib.fun import log


import poplib
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr


def print_info(msg, indent=0):
    if indent == 0:
        for header in ['From', 'To', 'Subject']:
            value = msg.get(header, '')
            if value:
                if header == 'Subject':
                    value = decode_str(value)
                else:
                    hdr, addr = parseaddr(value)
                    name = decode_str(hdr)
                    value = u'%s <%s>' % (name, addr)
            print('%s%s: %s' % ('  ' * indent, header, value))
    if (msg.is_multipart()):
        parts = msg.get_payload()
        for n, part in enumerate(parts):
            print('%spart %s' % ('  ' * indent, n))
            print('%s--------------------' % ('  ' * indent))
            print_info(part, indent + 1)
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/HTML':
            content = msg.get_payload(decode=True)
            charset = guess_charset(msg)
            if charset:
                content = content.decode(charset)
            print('%sText: %s' % ('  ' * indent, content + '...'))
        else:
            print('%sAttachment: %s' % ('  ' * indent, content_type))


def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
        return value


def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset


def login():
    email = "alex_command_bus@126.com"
    password = "YAYIYDJCOLBOSTGT"
    pop3_server = "pop.126.com"
    server = poplib.POP3(pop3_server)
    server.set_debuglevel(1)
    print(server.getwelcome().decode('utf-8'))
    server.user(email)
    server.pass_(password)
    return server


def load_mails():
    pass


class EmailServer():
    def __init__(self):
        self.server = login()

    def load_mails(self):
        resp, mails, octets = self.server.list()
        print(mails)

        # 获取最新一封邮件，索引号从1开始
        mails_count = len(mails)
        log(f'Email Count: {mails_count}')


        for index in range(mails_count):
            resp, lines, octets = self.server.retr(index)
            msg_content = b'\r\n'.join(lines).decode('utf-8')
            msg = Parser().parsestr(msg_content)

            print_info(msg)

    def delete_all():
        pass


server = EmailServer()
server.load_mails()