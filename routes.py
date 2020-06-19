import os
from flask import Blueprint,render_template,request
from CTFd.utils.decorators import authed_only,admins_only
from CTFd.utils.user import get_current_user
from . import models,utils
import requests
import time

#################writeup上传的路由################
writeup_blueprint = Blueprint("writeup", __name__)

@writeup_blueprint.route('/writeup', methods=['POST'])
@authed_only
def uplaod_writeup():
    try:
        file = request.files['writeup']
        challenge_id = request.form.get('challenge_id')
        challenge_name = request.form.get('challenge_name')
        challenge_folder = challenge_id+'_'+challenge_name
        uid = get_current_user().id
        username = get_current_user().name
        UPLOAD_FOLDER = os.path.join(os.getcwd(),'writeup',challenge_folder,username)
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        filename = utils.secure_filename(file.filename)
        print(filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        models.insert_writeup(challenge_id,uid,path)
        return 'Success'
    except:
        return 'Error'

@writeup_blueprint.route('/writeup',methods=['GET'])
@authed_only
def writeup_status():
    challenge_id = request.args.get("cid")
    uid = get_current_user().id
    wp = models.query_writeup(challenge_id,uid)
    if wp:
        return 'Uploaded'
    else:
        return 'Not uploaded'


####################动态部署的路由########################
dynamic_deploy_blueprint = Blueprint("dynamic_deploy", __name__)

@dynamic_deploy_blueprint.route('/test-connection',methods=['POST'])
@admins_only
def test_connection():
    try:
        url = request.form['url'] + '/test'
        passcode = request.form['passcode']
        data = {'passcode':passcode}
        response = requests.post(url=url,data=data).text
        if response == 'Success':
            return 'Success'
        else:
            raise
    except:
        return 'Error'

@dynamic_deploy_blueprint.route('/deploy',methods=['POST'])
@authed_only
def deploy():
    try:
        cid = request.form['challenge_id']
        uid = get_current_user().id
        start_time = time.time()

        # 检查该用户是否已经部署了container
        if models.query_container_uid(uid):
            return 'Repeat'

        challenge = models.query_FishChallengeTable(cid)
        if challenge:
            url = challenge.url + '/deploy'
            passcode = challenge.passcode
            data = {'uid':uid,'passcode':passcode}
            response = requests.post(url=url,data=data).text
            if response[0:7] == 'Success':
                con_url = response[8:]
                models.insert_container(cid,uid,start_time,con_url)
                return 'Success '+con_url+' '+'3600'
            raise
        else:
            raise
    except:
        return 'Error'

@dynamic_deploy_blueprint.route('/destroy',methods=['POST'])
@authed_only
def destroy():
    try:
        cid = request.form['challenge_id']
        uid = get_current_user().id

        # 检查该用户是否真的部署了container
        if models.query_container(cid,uid):
            fish_challenge = models.query_FishChallengeTable(cid)
            if fish_challenge:
                url = fish_challenge.url + '/destroy'
                passcode = fish_challenge.passcode
                data = {'uid':uid,'passcode':passcode}
                response = requests.post(url=url,data=data).text
                if response == 'Success':
                    models.delete_containter(cid,uid)
                    return 'Success'
            raise
        else:
            raise
    except:
        return 'Error'

@dynamic_deploy_blueprint.route('/renew',methods=['POST'])
@authed_only
def renew():
    try:
        cid = request.form['challenge_id']
        uid = get_current_user().id
        start_time = time.time()

        # 检查该用户是否真的部署了container
        if models.query_container(cid,uid):
            models.alter_containter(cid,uid,start_time)
            return 'Success'
        else:
            raise
    except:
        return 'Error'

@dynamic_deploy_blueprint.route('/status',methods=['POST'])
@authed_only
def status():
    try:
        cid = request.form['challenge_id']
        uid = get_current_user().id
        now = time.time()
        con = models.query_container(cid,uid)

        # 检查该用户是否真的部署了container
        if con:
            left_time = str(int(3600 - (now-con.start_time))) # 返回剩余时间
            con_url = con.url
            return 'Success '+con_url+' '+left_time
        else:
            return 'No'
    except:
        return 'Error'