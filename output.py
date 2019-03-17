# coding: utf-8
from jikescrapy.settings import REDIS_CONFIG, REDIS_KEYS
import redis
from py2neo import Database, Graph, NodeMatcher
from py2neo.data import Node, Relationship


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
            print(k)
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


if __name__ == '__main__':
    mg = MyGraph()
    # print(mg.mather.match('JIKE_user', name='flythief'))
    # mg.flush()
    mg.dump()


