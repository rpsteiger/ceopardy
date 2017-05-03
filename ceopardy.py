# Ceopardy
# https://github.com/obilodeau/ceopardy/
#
# Olivier Bilodeau <olivier@bottomlesspit.org>
# Copyright (C) 2017 Olivier Bilodeau
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
import functools
import logging
import random
import re
import sys

from flask import g, Flask, render_template, redirect, jsonify, request
from flask_socketio import SocketIO, emit, disconnect
from flask_sqlalchemy import SQLAlchemy

from config import config
from forms import TeamNamesForm, TEAM_FIELD_ID

VERSION = "0.1.0"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Alex Trebek forever!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ceopardy.db'
# To supress warnings about a feature we don't use
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app)
db = SQLAlchemy(app)


@app.context_processor
def inject_config():
    """Injects ceopardy configuration for the template system"""
    return config


@app.route('/')
@app.route('/viewer')
def viewer():
    controller = get_controller()
    categories = controller.get_categories()
    teams = controller.get_teams_score()
    questions = controller.get_questions_status_for_viewer()
    state = controller.get_complete_state()
    return render_template('viewer.html', teams=teams, categories=categories,
                           questions=questions, state=state)
    # FIXME: fchar: is there a way to socketio a board update right after this?


# TODO we must kill all client-side state on server load.
# To reproduce: Not-reloading a host view and reloading server causes mismatch
# between client and server states. Client is out of sync.
# TODO add authentication here
@app.route('/host')
def host():
    controller = get_controller()
    if not controller.is_game_in_progress():
        must_init = controller.is_game_initialized() is False
        return render_template('start.html', must_init=must_init)
    teams = controller.get_teams_for_form()
    form = TeamNamesForm(data=teams)
    questions = controller.get_questions_status_for_host()
    state = controller.get_complete_state()
    return render_template('host.html', form=form, teams=teams,
                           questions=questions, state=state)


# For now, this will give un an initial state which will avoid complications when
# rendering the host board
@app.route('/init', methods=["POST"])
def init():
    """Init can resume a finished game or start a new one"""
    controller = get_controller()

    if request.form['action'] == "new":
        teamnames = {}
        for i in range(1, config['NB_TEAMS'] + 1):
            teamnames['team{}'.format(i)] = 'Team {}'.format(i)
        try:
            controller.setup_teams(teamnames)
            controller.setup_questions()
            controller.start_game()
        except:
            return jsonify(result="failure", error="Initialization error!")

    elif request.form['action'] == "resume":
        controller.resume_game()

    # This is kind of dirty, not sure I like it
    content = "<p>{}</p>".format(config["MESSAGES"][0]["text"])
    controller.set_state("message", "message1")
    controller.set_state("overlay-big", content)
    emit("overlay", {"action": "show", "id": "big", "html": content},
         namespace='/viewer', broadcast=True)

    return jsonify(result="success")


@app.route('/setup', methods=["POST"])
def setup():
    controller = get_controller()
    form = TeamNamesForm()
    # TODO: [LOW] csrf token errors are not logged (and return 200 which contradicts docs)
    if not form.validate_on_submit():
        return jsonify(result="failure", errors=form.errors)
    teamnames = {field.id: field.data for field in form
                 if TEAM_FIELD_ID in field.flags}
    controller.update_teams(teamnames)
    emit("team", {"action": "name", "args": teamnames}, namespace='/viewer', broadcast=True)
    return jsonify(result="success", teams=teamnames)


@app.route('/answer', methods=["POST"])
def answer():
    # FIXME this form isn't CSRF protected
    app.logger.debug("Answer form has been submitted with: {}", request.form)
    data = request.form
    controller = get_controller()
    app.logger.debug('received data: {}'.format(data["id"]))
    # FIXME turn this into a function, it's redundant
    match = re.match("c([0-9]+)q([0-9]+)", data["id"])
    if match is None:
        return jsonify(result="failure", error="Invalid category/question format!")
    col, row = match.groups()
    question_text = controller.get_question(col, row)
    # Send everything but qid as a dict
    answers = request.form.to_dict()
    answers.pop('id')
    if not controller.answer_normal(col, row, answers):
        return jsonify(result="failure", error="Answer submission failed!")
    # TODO this is grossly inefficient
    question_status = controller.get_questions_status_for_host()
    teams = controller.get_teams_score_by_tid()
    emit("team", {"action": "score", "args": teams}, namespace='/viewer', broadcast=True)
    return jsonify(result="success", answers=question_status[data["id"]])
    

@socketio.on('question', namespace='/host')
def handle_question(data):
    controller = get_controller()
    if data["action"] == "select":
        match = re.match("c([0-9]+)q([0-9]+)", data["id"])
        if match is None:
            return ""
        col, row = match.groups()
        question = controller.get_question(col, row)
        answer = controller.get_answer(col, row)
        emit("overlay", {"action": "show", "id": "small", "html": question},
             namespace='/viewer', broadcast=True)
        controller.set_state("question", data["id"])
        controller.set_state("overlay-small", question)
        return {"question": question, "answer": answer}
    elif data["action"] == "deselect":
        state = controller.get_questions_status_for_viewer()
        emit("update-board", state, namespace='/viewer', broadcast=True)
        emit("overlay", {"action": "hide", "id": "small", "html": ""}, namespace='/viewer', broadcast=True)
        controller.set_state("question", "")
        controller.set_state("overlay-small", "")
        return {}


@socketio.on('message', namespace='/host')
def handle_message(data):
    controller = get_controller()
    # FIXME Temporary XSS!!!
    if data["action"] == "show":
        content = "<p>{0}</p>".format(data["text"])
        mid = data["id"]
        emit("overlay", {"action": "show", "id": "big", "html": content}, 
            namespace='/viewer', broadcast=True)
    else:
        content = ""
        mid = ""
        emit("overlay", {"action": "hide", "id": "big", "html": ""}, 
            namespace='/viewer', broadcast=True)
    controller.set_state("message", mid)
    controller.set_state("overlay-big", content)


@socketio.on('team', namespace='/host')
def handle_team(data):
    controller = get_controller()
    if data["action"] == "select":
        data["args"] = data["id"]
        controller.set_state("team", data["id"])
    elif data["action"] == "roulette":
        nb = controller.get_nb_teams()
        l = []
        team = "team" + str(random.randrange(1, nb + 1))
        for i in range(12):
            l.append("team" + str(i % nb + 1))
        l.append(team)
        data["args"] = l
        controller.set_state("team", team)
    else:
        return
    emit("team", data, namespace='/viewer', broadcast=True)


@socketio.on('slider', namespace='/host')
def handle_slider(data):
    controller = get_controller()
    controller.set_state(data["id"], data["value"])


@socketio.on('final', namespace='/host')
def move_to_final_round(data):
    controller = get_controller()

    if controller.is_final_question():
        # TODO implement
        pass
    else:
        # TODO better highlight winner
        text = "<p>That's all folks! Thanks for playing!</p>"
        controller.set_state("overlay-small", text)
        controller.finish_game()
        emit("overlay", {"action": "show", "id": "small", "html": text},
             namespace='/viewer', broadcast=True)


@socketio.on('refresh', namespace='/viewer')
def handle_refresh():
    controller = get_controller()
    # FIXME
    #state = controller.dictionize_questions_solved()
    state = {}
    emit("update-board", state)


if __name__ == '__main__':

    # Logging
    file_handler = logging.FileHandler('ceopardy.log')
    #file_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        '{asctime} {levelname}: {message} [in {pathname}:{lineno}]', style='{')
    file_handler.setFormatter(fmt)
    app.logger.addHandler(file_handler)

    # Cleaner controller access
    # Unsure if required once we have a db back-end
    with app.app_context():

        from controller import Controller
        def get_controller():
            _ctl = getattr(g, '_ctl', None)
            if _ctl is None:
                _ctl = g._ctl = Controller()
            return _ctl

        @app.teardown_appcontext
        def teardown_controller(exception):
            #app.logger.debug("Controller teardown requested")
            _ctl = getattr(g, '_ctl', None)
            if _ctl is not None:
                _ctl = None

    # WARNING: This app is not ready to be exposed on the network.
    #          Game host interface would be exposed.
    socketio.run(app, host="127.0.0.1", debug=True)
