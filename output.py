# coding: utf-8
from jikescrapy.settings import REDIS_CONFIG, REDIS_KEYS, START_USERNAME, MYSQL_URI
import redis
from py2neo import Database, Graph, NodeMatcher
from py2neo.data import Node, Relationship
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from model import JikeUser
import time


class MyGraph(object):
    def __init__(self):
        self.graph = Graph('bolt://localhost:7687', user='neo4j', password='lzjlzj123')
        self.mather = NodeMatcher(self.graph)
        pool = redis.ConnectionPool(**REDIS_CONFIG)
        self.rds = redis.StrictRedis(connection_pool=pool)
        self.username, self.screenName = self.get_main_user_info()
        self.user_info = {
            "username": self.username,
            "screenName": self.screenName
        }
        self.node_name = 'JIKE_user'

    def get_main_user_info(self):
        # return self.rds.hget(REDIS_KEYS.get('user_info_key'), 'username'),\
        #        self.rds.hget(REDIS_KEYS.get('user_info_key'), 'screenName')
        return '82D23B32-CF36-4C59-AD6F-D05E3552CBF3', '瓦恁'

    def get_followers(self, username):
        follower_key = REDIS_KEYS.get('follower_key').format(username)
        followers = self.rds.hgetall(follower_key)
        for k, v in followers.items():
            yield k, eval(v)

    def dump_key(self, follower_key):
        self.rds.dump(follower_key)

    def flush(self):
        self.graph.delete_all()

    def push_into_graph(self, user_info):
        tx = self.graph.begin()
        username = user_info.get('username')
        screenName = user_info.get('screenName')
        if not self.mather.match(self.node_name, name=screenName):
            root_node = Node(self.node_name, name=screenName)
            tx.create(root_node)
        else:
            root_node = self.mather.match(self.node_name, name=screenName).first()
        for k, v in self.get_followers(username):
            if not self.mather.match(self.node_name, name=v.get('screenName')):
                node = Node(self.node_name, name=v.get('screenName'))
                print('my create', node)
                tx.create(node)
            else:
                node = self.mather.match(self.node_name, name=v.get('screenName')).first()
                print(node)
            tx.create(Relationship(node, 'FOLLOWER', root_node))
        tx.commit()

    def dump(self):
        self.push_into_graph(self.user_info)
        for k, v in self.get_followers(self.username):
            self.push_into_graph(
                {
                    "username": k,
                    "screenName": v.get('screenName')
                }
            )


class MyRedis(object):
    def __init__(self):
        pool = redis.ConnectionPool(**REDIS_CONFIG)
        self.rds = redis.StrictRedis(connection_pool=pool)

    def get_follower(self, username):
        follower_key = REDIS_KEYS.get('follower_key').format(username)
        followers = self.rds.smembers(follower_key)
        for follower in followers:
            yield follower

    def get_info(self, username):
        user_info_hash_key = REDIS_KEYS.get("user_info_hash_key").format(username)
        user_info = self.rds.hgetall(user_info_hash_key)
        return user_info

    def get_all_username(self):
        cur = self.load_cur()
        print(cur)
        cur, results = self.rds.scan(cur, match='*user_info', count=10)
        yield [self.get_info(username.strip("_user_info")) for username in results]
        while cur != 0:
            self.dom_cur(cur)
            cur, results = self.rds.scan(cur, match='*user_info', count=10)
            results = [self.get_info(username.strip("_user_info")) for username in results]
            yield [result for result in results if result]

    @staticmethod
    def dom_cur(cur):
        with open('cur', 'w') as f:
            f.write(str(cur))

    @staticmethod
    def load_cur():
        try:
            with open('cur') as f:
                return int(f.read().strip('\n'))
        except Exception as e:
            print(e)
            return 0


class MyMysql(object):
    def __init__(self):
        engine = create_engine(MYSQL_URI)
        self.Session = sessionmaker(bind=engine)
        self.Scoped_session = sessionmaker(bind=engine)

    @staticmethod
    def convert_time(time_str):
        try:
            return int(time.mktime(time.strptime(time_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')))
        except Exception as e:
            return 0

    def dom_user_info(self, user_info):
        if self.search_info(user_info.get("username")):
            return
        jike_user = JikeUser(
            username=user_info.get("username") if user_info.get("username") else '',
            briefIntro=user_info.get("briefIntro") if user_info.get("briefIntro") else '',
            city=user_info.get('city') if user_info.get('city') != 'None' else '',
            country=user_info.get('country') if user_info.get('country') != 'None' else '',
            createdAt=user_info.get('createdAt') if user_info.get('createdAt') else '',
            create_at_int=self.convert_time(user_info.get('createdAt')),
            gender=user_info.get('gender') if user_info.get('gender') else '',
            isVerified=1 if user_info.get('isVerified') != 'False' else 0,
            profileImageUrl=user_info.get('profileImageUrl') if user_info.get('profileImageUrl') else '',
            province=user_info.get('province') if user_info.get('province') != 'None' else '',
            ref=user_info.get('ref') if user_info.get('ref') else '',
            screenName=user_info.get('screenName') if user_info.get('screenName') else '',
            updatedAt=user_info.get('updatedAt') if user_info.get('updatedAt') else '',
            update_at_int=self.convert_time(user_info.get('update_at_int')),
            verifyMessage=user_info.get('verifyMessage') if user_info.get('verifyMessage') else ''
        )
        try:
            session = self.Session()
            session.add(jike_user)
            session.commit()
        except Exception as e:
            print(e)

    def dom_users_info(self, users):
        us = []
        for user_info in users:
            jike_user = JikeUser(
                username=user_info.get("username") if user_info.get("username") else '',
                briefIntro=user_info.get("briefIntro") if user_info.get("briefIntro") else '',
                city=user_info.get('city') if user_info.get('city') != 'None' else '',
                country=user_info.get('country') if user_info.get('country') != 'None' else '',
                createdAt=user_info.get('createdAt') if user_info.get('createdAt') else '',
                create_at_int=self.convert_time(user_info.get('createdAt')),
                gender=user_info.get('gender') if user_info.get('gender') else '',
                isVerified=1 if user_info.get('isVerified') != 'False' else 0,
                profileImageUrl=user_info.get('profileImageUrl') if user_info.get('profileImageUrl') else '',
                province=user_info.get('province') if user_info.get('province') != 'None' else '',
                ref=user_info.get('ref') if user_info.get('ref') else '',
                screenName=user_info.get('screenName') if user_info.get('screenName') else '',
                updatedAt=user_info.get('updatedAt') if user_info.get('updatedAt') else '',
                update_at_int=self.convert_time(user_info.get('update_at_int')),
                verifyMessage=user_info.get('verifyMessage') if user_info.get('verifyMessage') else ''
            )
            us.append(jike_user)
        try:

            session = self.Session()
            session.add_all(us)
            session.commit()
            # print('add success {}'.format("/".join([u.get("username") for u in users])))
        except Exception as e:
            with open('error.log', 'a+') as f:
                f.write(str(e) + "\n\n\n")

    def get_all_users(self):
        session = self.Session()
        for user in session.query(JikeUser).all():
            yield user

    def search_info(self, username):
        session = self.Scoped_session()
        user = session.query(JikeUser).filter_by(
            username=username
        ).first()
        return user


if __name__ == '__main__':
    mr = MyRedis()
    mm = MyMysql()
    # for user in mm.get_all_users():
    #     print(mr.rds.delete(user.username + "_user_info"))
    us = []
    for results in mr.get_all_username():
        mm.dom_users_info(results)



