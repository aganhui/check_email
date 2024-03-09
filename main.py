from check_email import VerifyAgent

if __name__ == "__main__":
    EMAIL_ADDRESS = 'Keshen29@outlook.com'
    EMAIL_PASSWORD = 'sansheng608'
    agent = VerifyAgent(EMAIL_ADDRESS, EMAIL_PASSWORD)
    # code_list = agent.wait_for_verification_code(filter={
    #     "time_range": {
    #         "start": "2024-02-01 00:00:00",
    #     },
    # }, timeout=80)
    code_list = agent.wait_for_twitter_verification_code(filter={
        # "from": [ "907402005@qq.com" ],
        "time_range": {
            "start": "2024-03-09 10:00:00",
        },
    }, timeout=80)
    if isinstance(code_list, list):
        for code in code_list:
            print(f"verification code: {code}")

    