import os
from flask import Blueprint,render_template,request
from CTFd.utils.decorators import authed_only,admins_only
from CTFd.utils.user import get_current_user
from . import models,utils
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
        url = request.form['url']
        passcode = request.form['passcode']
        if utils.do_test_connection(url,passcode):
            return 'Success'
        else:
            return 'Error'
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
            url = challenge.url
            passcode = challenge.passcode
            con_url = utils.do_deploy(url,uid,passcode)
            if con_url:
                models.insert_container(cid,uid,start_time,con_url)
                return 'Success '+con_url+' '+'3600'
        return 'Error'
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
                url = fish_challenge.url
                passcode = fish_challenge.passcode
                if utils.do_destroy(url,uid,passcode):
                    models.delete_containter(cid,uid)
                    return 'Success'
        return 'Error'
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
        return 'Error'
    except:
        return 'Error'

@dynamic_deploy_blueprint.route('/status',methods=['GET'])
@authed_only
def status():
    try:
        cid = request.args['challenge_id']
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