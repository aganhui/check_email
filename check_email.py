

import imaplib
import email
from email.header import decode_header
import time
import re

class EmailData:
    def __init__(self, from_address, to_address, date_time, subject, plain_text_body):
        self.from_address = from_address
        self.to_address = to_address
        self.date_time = date_time
        self.subject = subject
        self.plain_text_body = plain_text_body

    def get_verification_code(self):
        # get verification code from subject
        # subject examples:
        # 1. 87ab46 is your X verification code
        # 2. Your Twitter confirmation code is 62v3cc5t
        # 3. Your verification code is: 1qk@456
        
        # 定义可能的提示文本模式
        patterns = [
            # r'(?<=is your)\b[A-Za-z0-9@#]{6,}',
            # r'(?<=Your Twitter confirmation code is)\b[A-Za-z0-9]{6,}',
            r'(?<=Your Twitter confirmation code is )\b[A-Za-z0-9]{6,}',
            r'(?<=Your X confirmation code is )\b[A-Za-z0-9]{6,}',
            r'[A-Za-z0-9]{6,}\b(?= is your X verification code)',
            # 添加更多模式以匹配不同的验证码提示文本
        ]

        # 遍历所有模式并尝试匹配
        for pattern in patterns:
            match = re.search(pattern, self.subject)
            if match:
                return match.group(0)

        return None    # 如果没有匹配项

class EmailDriver:
    def __init__(self, email_address, email_password):
        self.email_address = email_address
        self.email_password = email_password
        self.mail = imaplib.IMAP4_SSL('outlook.office365.com')
        self.mail.login(email_address, email_password)
        self.mail.select("Inbox")

    def __del__(self):
        # self.mail.close()
        # self.mail.logout()
        pass

    def get_all_email(self, filter=None):
        """
        filter example:
        {
            "from": [ "xxx@xx.com", "xxx@xx.com" ],
            "time_range": {
                "start": "2023-11-25 00:00:00",
                "end": "2023-11-26 00:00:00"
            },
            "subject": [ "xxx", "xxx" ]
        }
        """
        email_data_list = []
        status, messages = self.mail.search(None, 'ALL')  # 返回所有邮件的ID列表
        for i in messages[0].split():
            try:
                status, message = self.mail.fetch(i, "(RFC822)")
                raw_email = message[0][1]

                # 解析邮件发送方，并过滤
                email_message = email.message_from_bytes(raw_email)
                from_header = email_message['From']
                from_address = decode_header(from_header)[0][0]
                if isinstance(from_address, bytes):
                    from_address = from_address.decode()
                email_address = from_address.split("<")[-1].split(">")[0]
                if "from" in filter:
                    if email_address not in filter["from"]:
                        continue

                # 解析邮件时间，并过滤
                date_header = email_message['Date']
                date_time = decode_header(date_header)[0][0]
                if isinstance(date_time, bytes):
                    date_time = date_time.decode()
                if "time_range" in filter:
                    time_received = time.strptime(date_time, "%a, %d %b %Y %H:%M:%S %z")
                    if "start" in filter["time_range"]:
                        if time_received < time.strptime(filter["time_range"]["start"], "%Y-%m-%d %H:%M:%S"):
                            continue
                    if "end" in filter["time_range"]:
                        if time_received > time.strptime(filter["time_range"]["end"], "%Y-%m-%d %H:%M:%S"):
                            continue

                # 解析邮件主题，并过滤
                subject = decode_header(email_message['Subject'])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                if "subject" in filter:
                    subject_in_filter = False
                    for subject_filter in filter["subject"]:
                        if subject_filter in subject:
                            subject_in_filter = True
                            break
                    if not subject_in_filter:
                        continue
                
                # 获取邮件正文
                plain_text_body = self.get_email_body(email_message)
            except Exception as e:
                print(e)
                continue
            email_data = EmailData(email_address, self.email_address, date_time, subject, plain_text_body)
            email_data_list.append(email_data)
        return email_data_list

    def get_email_body(self, email_message):
        body = ''
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode(part.get_content_charset())
                elif part.get_content_type() == 'text/html':
                    html_body = part.get_payload(decode=True).decode(part.get_content_charset())
                    pass
                elif part.get_content_type() == "multipart/alternative":
                    pass
        else:
            body = email_message.get_payload(decode=True).decode(email_message.get_content_charset())
        return body

class VerifyAgent:
    def __init__(self, email_address, email_password):
        self.email_address = email_address
        self.email_password = email_password
        self.email_driver = EmailDriver(email_address, email_password)

    def wait_for_twitter_verification_code(self, filter: dict=None, timeout=60):
        if "from" not in filter:
            filter.update({
                "from": [ "info@x.com" ],
            })
        return self.wait_for_verification_code(filter, timeout)

    def wait_for_verification_code(self, filter: dict=None, timeout=60):
        start_time = time.time()     # 需要注意时区一致性
        if "time_range" not in filter:
            filter.update({
                "time_range": {
                    "start": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
                }
            })
        print(f"filter: {filter}")
        while True:
            if time.time() - start_time > timeout:
                return None
            email_data_list = self.email_driver.get_all_email(filter=filter)
            if len(email_data_list) > 0:
                code_list = []
                for email in email_data_list:
                    code = email.get_verification_code()
                    if code:
                        code_list.append(code)
                if len(code_list) > 0:
                    return code_list
            time.sleep(5)


if __name__ == "__main__":
    # 邮件服务器的地址和端口
    IMAP_SERVER = 'outlook.office365.com'
    IMAP_PORT = 993

    # 邮件账户的用户名和密码
    EMAIL_ADDRESS = 'Keshen29@outlook.com'
    EMAIL_PASSWORD = 'sansheng608'

    # get all emails
    email_driver = EmailDriver(EMAIL_ADDRESS, EMAIL_PASSWORD)
    email_data_list = email_driver.get_all_email(filter={
        "from": [ "info@x.com" ],
        "time_range": {
            "start": "2024-02-01 00:00:00",
            # "end": "2024-03-08 00:00:00"
        },
        "subject": [ "code" ]
    })
    for email in email_data_list:
        print(email.from_address)
        print(email.to_address)
        print(email.date_time)
        print(email.subject)
        # print(email.plain_text_body)
        code = email.get_verification_code()
        print(f"verification code: {code}")
        print("=====================================")

