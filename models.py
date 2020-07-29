from CTFd.models import db,Challenges
import time

####################CTFd-Fish类型的challenge##########################
class FishChallengeTable(Challenges):
    __mapper_args__ = {"polymorphic_identity": "CTFd-Fish"}
    id = db.Column(None, db.ForeignKey("challenges.id"), primary_key=True)
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)
    url = db.Column(db.String(200),nullable=False)
    passcode = db.Column(db.String(200),nullable=False)

    def __init__(self, *args, **kwargs):
        super(FishChallengeTable, self).__init__(**kwargs)
        self.initial = kwargs["value"]

def query_FishChallengeTable(cid):
    fish_challenge = db.session.query(FishChallengeTable).filter_by(id=cid).first()
    return fish_challenge

######################动态部署的容器#######################
class Container(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    cid = db.Column(None,db.ForeignKey("challenges.id"),nullable=False)
    uid = db.Column(db.Integer,nullable=False)
    start_time = db.Column(db.Float,nullable=False)
    url = db.Column(db.String(200),nullable=False)

    def __init__(self,cid,uid,start_time,url):
        self.cid = int(cid)
        self.uid = int(uid)
        self.start_time = start_time
        self.url = url

def insert_container(cid,uid,start_time,url):
    con = Container(cid,uid,start_time,url)
    db.session.add(con)
    db.session.commit()

def query_container(cid,uid):
    return db.session.query(Container).filter_by(cid=cid,uid=uid).first()

def query_container_uid(uid):
    return db.session.query(Container).filter_by(uid=uid).first()

def query_container_expired():
    expired_containers = db.session.query(Container).filter(Container.start_time < time.time()-3600).all()
    return expired_containers

def delete_containter(cid,uid):
    db.session.query(Container).filter_by(cid=cid,uid=uid).delete()
    db.session.commit()

def delete_containter_special(con):
    con.delete()
    db.session.commit()

def alter_containter(cid,uid,start_time):
    con = db.session.query(Container).filter_by(uid=uid).first()
    con.start_time = start_time
    db.session.commit()

#########################上传的writeup######################
class Writeup(db.Model):
    wid = db.Column(db.Integer,primary_key=True)
    cid = db.Column(None,db.ForeignKey("challenges.id"),nullable=False)
    uid = db.Column(db.Integer,nullable=False)
    path = db.Column(db.String(200),nullable=False)

    def __init__(self,cid,uid,path):
        self.cid = int(cid)
        self.uid = int(uid)
        self.path = path

def insert_writeup(cid,uid,path):
    wp = Writeup(cid,uid,path)
    db.session.add(wp)
    db.session.commit()

def query_writeup(cid,uid):
    wp = db.session.query(Writeup).filter_by(cid=cid,uid=uid).first()
    return wp