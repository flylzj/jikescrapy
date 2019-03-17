# coding: utf-8
from jikescrapy.settings import REDIS_CONFIG, REDIS_KEYS, START_USERNAME, MYSQL_URI
import redis
from py2neo import Database, Graph, NodeMatcher
from py2neo.data import Node, Relationship
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
import time
from model import JikeUser


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
        return self.rds.hgetall(user_info_hash_key)


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
        jike_user = JikeUser(
            username=user_info.get("username"),
            briefIntro=user_info.get("briefIntro"),
            city=user_info.get('city'),
            country=user_info.get('country'),
            createdAt=user_info.get('createdAt'),
            create_at_int=self.convert_time(user_info.get('createdAt')),
            gender=user_info.get('gender'),
            isVerified=user_info.get('isVerified'),
            profileImageUrl=user_info.get('profileImageUrl'),
            province=user_info.get('province'),
            ref=user_info.get('ref'),
            screenName=user_info.get('screenName'),
            updatedAt=user_info.get('updatedAt'),
            update_at_int=self.convert_time(user_info.get('update_at_int')),
            verifyMessage=user_info.get('verifyMessage')
        )
        try:
            session = self.Session()
            session.add(jike_user)
            session.commit()
        except Exception as e:
            print(e)

    def dom_info_thread(self, user_info):
        if self.search_info(user_info.get("username")):
            return
        jike_user = JikeUser(
            username=user_info.get("username"),
            briefIntro=user_info.get("briefIntro"),
            city=user_info.get('city'),
            country=user_info.get('country'),
            createdAt=user_info.get('createdAt'),
            create_at_int=self.convert_time(user_info.get('createdAt')),
            gender=user_info.get('gender'),
            isVerified=user_info.get('isVerified'),
            profileImageUrl=user_info.get('profileImageUrl'),
            province=user_info.get('province'),
            ref=user_info.get('ref'),
            screenName=user_info.get('screenName'),
            updatedAt=user_info.get('updatedAt'),
            update_at_int=self.convert_time(user_info.get('update_at_int')),
            verifyMessage=user_info.get('verifyMessage')
        )
        try:
            session = self.Scoped_session()
            session.add(jike_user)
            session.commit()
        except Exception as e:
            return user_info.get("username")

    def search_info(self, username):
        session = self.Scoped_session()
        user = session.query(JikeUser).filter_by(
            username=username
        ).first()
        return user

    def dom_info_with_queue(self, follower_queue):
        while not follower_queue.empty():
            print("now queue size {}".format(follower_queue.qsize()))
            info = follower_queue.get()
            self.dom_info_thread(info)


if __name__ == '__main__':
    mr = MyRedis()
    # mm = MyMysql()
    # follower_queue = Queue()
    count = 0
    for follower in mr.get_follower(START_USERNAME):
        # follower_queue.put(mr.get_info(follower))
        mr.rds.sadd('jike_users', follower)
        for sec_follower in mr.get_follower(follower):
            mr.rds.sadd('jike_uesrs', sec_follower)
            # follower_queue.put(mr.get_info(sec_follower))
            count += 1
    print(count)

    # print("now queue size {}".format(follower_queue.qsize()))

    # for i in range(10):
    #     t = Thread(target=mm.dom_info_with_queue, args=(follower_queue, ))
    #     t.start()
    #
    # while not follower_queue.empty():
    #     continue



