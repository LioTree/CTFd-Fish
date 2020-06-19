from flask import Flask, render_template, request, make_response
import hashlib
import os
import subprocess
import random

app = Flask(__name__)

baseUrl = '' #服务器ip或域名
imageID = '' #需要启动的镜像id
innerPort = 5000 #docker内部端口
deployPort = 5000  #deployer的端口
startPort = 6000 #部署容器起始端口
endPort = 6010 #部署容器结束端口
protocol='http://'

runOrder = 'docker run -p {port}:{inPort} --rm -d {ID}' 
stopOrder = 'docker kill {ID}'

userDic = []

passcode = str(random.random()) 
portList = set(i for i in range(startPort, endPort))

containerDic = {}
'''
{
    user:
    [containerID,port]
}
'''
############路由#################

@app.route('/deploy',methods=['POST'])  # 部署验证
def deploy():
    if request.form['passcode'] == passcode:
        uid = request.form['uid']
        userDic.append(uid)
        return doDeply(uid)
    else:
        return "Fvck you Hacker!!"

@app.route("/destroy",methods=['POST'])  # 销毁验证
def destroy():
    if request.form['passcode'] == passcode:
        uid = request.form['uid']
        return dodestroy(uid)
    else:
        return "Fvck you Hacker!!"

##########辅助路由#####################
@app.route('/clear',methods=['POST'])
def clear():  # 全部清理
    if request.form['passcode'] == passcode:
        userDic.clear()
        order = 'docker ps'
        ret = os.popen(order).read().split('\n')[1:]
        for cont in ret:
            if imageID in cont:
                aimID = cont[:12]
                os.popen(stopOrder.format(ID=aimID))
        return "Success"
    else:
        return "Fvck you Hacker!!"

# 用来测试连接    
@app.route('/test',methods=['POST'])
def test():
    if request.form['passcode'] == passcode:
        return 'Success'
    else:
        return 'Error'


###########功能函数###################
def doDeply(uid):  # 部署
    try:
        if uid in containerDic.keys(): # 其实这步不需要了，会在CTFd上检查是否已部署
            port = containerDic[uid][1]
            return 'Success:{url}'.format(url=protocol+baseUrl+':'+str(port)+'/')# 直接跳
        choosePort = portList.pop()
        turl = protocol+baseUrl+':'+str(choosePort)+'/'
        containerSHA = os.popen(runOrder.format(
            port=choosePort, ID=imageID, inPort=innerPort)).read()
        containerDic[uid] = [containerSHA, choosePort]
        return 'Success:{url}'.format(url=turl)
    except:
        return 'Error'


def dodestroy(uid):  # 销毁
    if uid not in containerDic.keys():
        return "Error"
    else:
        removeUser(uid)
        id = dropUser(uid)
        stopContainer(id)
        return "Success"

def dropUser(uid):  # 接受一个uid, 将其从containerDic中移除, 将端口号push回未占用列表, 返回需要free的containerID
    container = containerDic[uid]
    port = container[1]
    id = container[0]
    containerDic.pop(uid)
    portList.add(port)
    return id


def stopContainer(id):
    try:
        os.popen(stopOrder.format(ID=id))
        return 1
    except:
        return 0

def removeUser(uid): # 彻底删除一个用户
    userDic.remove(uid)



if __name__ == "__main__":
    print('Your passcode is ' + passcode)
    app.run(host='0.0.0.0', port=deployPort, debug=0)
