# coding: utf-8
from jikescrapy.settings import REDIS_CONFIG, REDIS_KEYS, MYSQL_URI
import redis
from py2neo import  Graph, NodeMatcher
from py2neo.data import Node, Relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import JikeUser
import time
import csv
import re


class MyGraph(object):
    def __init__(self):
        self.graph = Graph('bolt://localhost:7687', user='neo4j', password='lzjlzj123')
        self.mather = NodeMatcher(self.graph)
        self.node_name = 'JIKE_user'
        self.FOLLOWER_REL = 'FOLLOWER'
        self.FOLLOWING_REL = 'FOLLOWING'

    def add_a_rel(self, node_a, node_b, rel_type='FOLLOWER'):
        ab = Relationship(node_a, rel_type, node_b)
        self.graph.create(ab)

    def add_a_person(self, user):
        if self.search_a_person(username=user.username):
            return
        node = Node(self.node_name, **user.to_dict())
        self.graph.create(node)

    def search_a_person(self, **properties):
        return self.mather.match(self.node_name, **properties).first()

    def flush(self):
        self.graph.delete_all()


class MyRedis(object):
    def __init__(self):
        pool = redis.ConnectionPool(**REDIS_CONFIG)
        self.rds = redis.StrictRedis(connection_pool=pool)

    def get_has_follow(self):
        for username in self.rds.scan_iter('*follow*'):
            yield re.split(r'_follow.*', username)[0], re.search(r'follow.*', username).group()
            # yield username.split("_")[0], username.split("_")[1]

    def get_follow(self, username, follow_type="follower"):
        if follow_type != 'follower' and follow_type != 'following':
            print(username, follow_type)
        follow_key = REDIS_KEYS.get('{}_key'.format(follow_type))[0].format(username)
        for follow_user in self.rds.sscan_iter(follow_key):
            yield follow_user


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

    def search_info(self, username):
        session = self.Scoped_session()
        user = session.query(JikeUser).filter_by(
            username=username
        ).first()
        session.close()
        return user

    def get_all_users(self):
        session = self.Scoped_session()
        for user in session.query(JikeUser).yield_per(1):
            yield user


class MyController():
    def __init__(self):
        self.mg = MyGraph()
        self.mr = MyRedis()
        self.mm = MyMysql()

    def dom_all_users(self):
        for user in self.mm.get_all_users():
            self.mg.add_a_person(user)

    def dom_relationship(self):
        for username, follow_type in self.mr.get_has_follow():
            for follow_username in self.mr.get_follow(username, follow_type):
                user_node = self.mg.search_a_person(username=username)
                follow_node = self.mg.search_a_person(username=follow_username)
                if not user_node or not follow_node:
                    with open("error.log", "a+", encoding='utf-8') as f:
                        f.write("{}{}{}".format(username, follow_type, follow_username))
                    continue
                if follow_type == 'follower':
                    self.mg.add_a_rel(follow_node, user_node, self.mg.FOLLOWER_REL)
                else:
                    self.mg.add_a_rel(user_node, follow_node, self.mg.FOLLOWING_REL)

    def dump_user_to_csv(self):
        headers = [":ID", "id", "name", "username", "isVerified", "gender", "screenName", "create_at_int", ":LABEL"]
        with open('node.csv', 'a+', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, headers)
            writer.writeheader()
            for user in self.mm.get_all_users():
                writer.writerow(user.to_dict())

    def dump_relationship_to_csv(self):
        headers = ["user1", "rel", "user2"]
        follower_writer = csv.DictWriter(open('follower.csv', "a+", encoding='utf-8', newline=''), headers)
        follower_writer.writeheader()
        following_writer = csv.DictWriter(open('following.csv', "a+", encoding='utf-8', newline=''), headers)
        following_writer.writeheader()
        for username, follow_type in self.mr.get_has_follow():
            for follow_username in self.mr.get_follow(username, follow_type):
                # user_node = self.mg.search_a_person(username=username)
                # follow_node = self.mg.search_a_person(username=follow_username)
                # if not user_node or not follow_node:
                #     with open("error.log", "a+", encoding='utf-8') as f:
                #         f.write("{}{}{}".format(username, follow_type, follow_username))
                #     continue

                if follow_type == 'follower':
                    follower_writer.writerow(
                            {
                                "user1": username,
                                "rel": self.mg.FOLLOWER_REL,
                                "user2": follow_username
                            }
                        )
                    # self.mg.add_a_rel(follow_node, user_node, self.mg.FOLLOWER_REL)
                else:
                    following_writer.writerow(
                            {
                                "user2": username,
                                "rel": self.mg.FOLLOWING_REL,
                                "user1": follow_username
                            }
                        )
                    # self.mg.add_a_rel(user_node, follow_node, self.mg.FOLLOWING_REL)


if __name__ == '__main__':
    mc = MyController()
    # mc.dom_all_users()
    mc.dump_relationship_to_csv()


