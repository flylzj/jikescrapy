# coding: utf-8
import requests
import pickle
import qrcode


def make_qrcode(api):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(api)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save('qrcode.png')


class JIKELoginer(object):
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
        }
        self.session_api = 'https://app.jike.ruguoapp.com/sessions.create'
        self.wait_for_login_api = 'https://app.jike.ruguoapp.com/sessions.wait_for_login?uuid={}'
        self.wait_for_confirmation_api = 'https://app.jike.ruguoapp.com/sessions.wait_for_confirmation?uuid={}'
        self.qrcode_api = 'jike://page.jk/web?url=https%3A%2F%2Fruguoapp.com%2Faccount%2Fscan%3F' \
                          'uuid%3D{}&displayHeader=false&displayFooter=false'
        self.profile_api = 'https://app.jike.ruguoapp.com/1.0/users/profile'
        self.refresh_token_api = 'https://app.jike.ruguoapp.com/app_auth_tokens.refresh'
        self.token = {}
        self.profile = {}

    def jike_login(self):
        self.token = self.load_token_from_file()
        if not self.token:
            print('重新扫码登录')
            self.login()
        else:
            print('从文件中加载token成功, 正在验证token是否过期')
            if not self.get_profile():
                print('token过期, 正在刷新token')
                token = self.refresh_token()
                if not token:
                    print('刷新token失败\n正在尝试重新扫码登录')
                    self.login()
                else:
                    print('刷新token成功')
                    self.token = token
                    self.get_profile()
        print('登陆成功, 登录用户名为: {} 昵称为: {}'.format(
            self.profile.get("user").get("username"),
            self.profile.get("user").get("screenName")
        ))

    def refresh_token(self):
        try:
            h = self.headers.copy()
            h.update(
                {
                    "x-jike-refresh-token": self.token.get("x-jike-refresh-token")
                }
            )
            r = requests.get(self.refresh_token_api, headers=h)
            return r.json()
        except Exception as e:
            return False

    def load_token_from_file(self):
        try:
            with open('token.pickle', 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print('获取token失败 {}'.format(e))
            return None

    def dump_token_to_file(self):
        try:
            with open('token.pickle', 'wb') as f:
                pickle.dump(self.token, f)
                return True
        except Exception as e:
            print('保存token失败, {}'.format(e))
            return False

    def make_token_headers(self):
        headers = self.headers.copy()
        headers.update(
            {
                "x-jike-access-token": self.token.get("x-jike-access-token")
            }
        )
        return headers

    def get_uuid(self):
        try:
            r = requests.get(self.session_api, headers=self.headers)
            return r.json().get("uuid")
        except Exception as e:
            print('get uuid error', e)
            return None

    def wait_for_login(self, uuid):
        try:
            print('start get', uuid)
            r = requests.get(self.wait_for_login_api.format(uuid), headers=self.headers, timeout=20)
            return r.json().get("logged_in")
        except Exception as e:
            return False

    def wait_for_confirmation(self, uuid):
        try:
            r = requests.get(self.wait_for_confirmation_api.format(uuid), headers=self.headers, timeout=20)
            return r.json()
        except Exception as e:
            return None

    def login(self):
        uuid = self.get_uuid()
        if not uuid:
            return
        print("获取uuid成功, 等待扫码")
        make_qrcode(self.qrcode_api.format(uuid))
        if not self.wait_for_login(uuid):
            return
        print("扫码成功,等待验证")
        self.token = self.wait_for_confirmation(uuid)
        if not self.token:
            exit(1)
        print('登录成功')
        self.profile = self.get_profile()
        self.dump_token_to_file()

    def get_profile(self):
        try:
            r = requests.get(self.profile_api, headers=self.make_token_headers())
            self.profile = r.json()
            return r.json().get("user")
        except Exception as e:
            print('获取个人信息失败, {}'.format(e))
            return


class JIKE(JIKELoginer):
    def __init__(self):
        super().__init__()
        self.follower_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/getFollowerList'
        self.subscribed_list_api = 'https://app.jike.ruguoapp.com/1.0/users/topics/listSubscribed'
        self.subscribed_status_api = 'https://app.jike.ruguoapp.com/1.0/users/topics/changeSubscriptionStatus'
        self.follow_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/follow'
        self.unfollow_api = 'https://app.jike.ruguoapp.com/1.0/userRelation/unfollow'
        self.jike_login()

    def change_follow_status(self, username, api):
        try:
            data = {
                "username": username
            }
            r = requests.post(api, headers=self.make_token_headers(), json=data)
            print(r.text)
            return r.json().get('success')
        except Exception as e:
            print('change follow status', e)
            return False

    def get_follower(self, username, more_key=None):
        try:
            # {"loadMoreKey":null,"username":"6ef2cacc-f140-4e75-a60c-686808ef7c2b","limit":20}
            data = {
                "loadMoreKey": more_key if isinstance(more_key, dict) else None,
                "username": username,
                "limit": 20
            }
            r = requests.post(self.follower_api, headers=self.make_token_headers(), json=data)
            return r.json()
        except Exception as e:
            print('get_follower error', e)
            return None

    def get_all_followers(self, username):
        more_key = 1
        while more_key:
            data = self.get_follower(username, more_key)
            if data:
                more_key = data.get('loadMoreKey')
                for d in data.get('data'):
                    yield d

    def get_subscribed(self, username, more_key=None):
        try:
            # {"loadMoreKey":null,"username":"6ef2cacc-f140-4e75-a60c-686808ef7c2b","limit":20}
            data = {
                "loadMoreKey": more_key,
                "username": username,
                "limit": 20
            }
            r = requests.post(self.subscribed_list_api, headers=self.make_token_headers(), json=data)
            datas = r.json().get("data")
            for data in datas:
                print(
                    data.get('id'),
                    data.get('type'),
                    data.get('messagePrefix'),
                    data.get("topicId"),
                    data.get("briefIntro")
                )
                if self.change_subscribed_status(data.get("id")):
                    print('退出圈子{}成功'.format(data.get("messagePrefix")))
                else:
                    print('退出圈子{}失败'.format(data.get("messagePrefix")))
            return r.json().get("loadMoreKey")
        except Exception as e:
            print(e)

    def change_subscribed_status(self, topic_id):
        try:
            data = {
                "topicObjectId": topic_id,
                "subscribed": False,
                "push": False
            }
            r = requests.post(self.subscribed_status_api, headers=self.make_token_headers(), json=data)
            print(r.json())
            return r.json().get("success")
        except Exception as e:
            print('change_subscribed_status error, {}'.format(e))
            return None


if __name__ == '__main__':
    jike = JIKE()
    wa_username = '82D23B32-CF36-4C59-AD6F-D05E3552CBF3'
    for d in jike.get_all_followers(wa_username):
        print(d.get('screenName'))
