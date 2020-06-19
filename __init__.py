from __future__ import division  # Use floating point for math calculations

import math

from flask import Blueprint,render_template,request

from CTFd.models import (
    ChallengeFiles,
    Challenges,
    Fails,
    Flags,
    Hints,
    Solves,
    Tags,
    db,
)
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.flags import get_flag_class
from CTFd.utils.modes import get_model
from CTFd.utils.uploads import delete_file
from CTFd.utils.user import get_ip
from flask_apscheduler import APScheduler

from . import routes,models,utils
import requests


class FishChallenge(BaseChallenge):
    id = "CTFd-Fish"  # Unique identifier used to register challenges
    name = "CTFd-Fish"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/CTFd_Fish/assets/create.html",
        "update": "/plugins/CTFd_Fish/assets/update.html",
        "view": "/plugins/CTFd_Fish/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/CTFd_Fish/assets/create.js",
        "update": "/plugins/CTFd_Fish/assets/update.js",
        "view": "/plugins/CTFd_Fish/assets/view.js",
        "writeup": "/plugins/CTFd_Fish/assets/writeup.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/CTFd_Fish/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "CTFd-Fish",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )

    @classmethod
    def calculate_value(cls, challenge):
        Model = get_model()

        solve_count = (
            Solves.query.join(Model, Solves.account_id == Model.id)
            .filter(
                Solves.challenge_id == challenge.id,
                Model.hidden == False,
                Model.banned == False,
            )
            .count()
        )

        # If the solve count is 0 we shouldn't manipulate the solve count to
        # let the math update back to normal
        if solve_count != 0:
            # We subtract -1 to allow the first solver to get max point value
            solve_count -= 1

        # It is important that this calculation takes into account floats.
        # Hence this file uses from __future__ import division
        value = (
            ((challenge.minimum - challenge.initial) / (challenge.decay ** 2))
            * (solve_count ** 2)
        ) + challenge.initial

        value = math.ceil(value)

        if value < challenge.minimum:
            value = challenge.minimum

        challenge.value = value
        db.session.commit()
        return challenge

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
        challenge = models.FishChallengeTable(**data)

        db.session.add(challenge)
        db.session.commit()

        return challenge

    @staticmethod
    def read(challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = models.FishChallengeTable.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": FishChallenge.id,
                "name": FishChallenge.name,
                "templates": FishChallenge.templates,
                "scripts": FishChallenge.scripts,
            },
        }
        return data

    @staticmethod
    def update(challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()

        for attr, value in data.items():
            # We need to set these to floats so that the next operations don't operate on strings
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        return FishChallenge.calculate_value(challenge)

    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.

        :param challenge:
        :return:
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        models.FishChallengeTable.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()

        # 删除该challenge动态部署的container
        models.Container.query.filter_by(cid=challenge.id).delete()
        # writeup的记录就不删了
        db.session.commit()

    @staticmethod
    def attempt(challenge, request):
        """
        This method is used to check whether a given input is right or wrong. It does not make any changes and should
        return a boolean for correctness and a string to be shown to the user. It is also in charge of parsing the
        user's input from the request itself.

        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return: (boolean, string)
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        flags = Flags.query.filter_by(challenge_id=challenge.id).all()
        for flag in flags:
            if get_flag_class(flag.type).compare(flag, submission):
                return True, "Correct"
        return False, "Incorrect"

    @staticmethod
    def solve(user, team, challenge, request):
        """
        This method is used to insert Solves into the database in order to mark a challenge as solved.

        :param team: The Team object from the database
        :param chal: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        challenge = models.FishChallengeTable.query.filter_by(id=challenge.id).first()
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        solve = Solves(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(req=request),
            provided=submission,
        )
        db.session.add(solve)
        db.session.commit()

        FishChallenge.calculate_value(challenge)

    @staticmethod
    def fail(user, team, challenge, request):
        """
        This method is used to insert Fails into the database in order to mark an answer incorrect.

        :param team: The Team object from the database
        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        wrong = Fails(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(request),
            provided=submission,
        )
        db.session.add(wrong)
        db.session.commit()
        db.session.close()


def load(app):
    # upgrade()
    app.db.create_all()
    CHALLENGE_CLASSES["CTFd-Fish"] = FishChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/CTFd_Fish/assets/"
    )
    app.register_blueprint(routes.writeup_blueprint)
    app.register_blueprint(routes.dynamic_deploy_blueprint)

    def auto_clean_container():
        with app.app_context():
            expired_containers = models.query_container_expired()
            if expired_containers:
                for con in expired_containers:
                    cid = con.cid
                    uid = con.uid
                    fish_challenge = models.query_FishChallengeTable(cid)
                    url = fish_challenge.url + '/destroy'
                    passcode = fish_challenge.passcode
                    data = {'uid':uid,'passcode':passcode}
                    requests.post(url=url,data=data)
                    models.delete_containter(cid,uid)

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='auto-clean', func=auto_clean_container, trigger="interval", seconds=10)