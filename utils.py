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
import glob
import html
import json
import os
import re
import csv

from config import config


def parse_questions(filename):
    """Parses a question file.
       Returns a dict (of categories) of lists of questions (in score order)
    """
    # TODO should drop the old format entirely?
    # if so use html and integrate answers into question file
    # people can then use asciidoctor or markdown to render questions from
    # a simpler format
    questions = {}
    cur_category = None
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.rstrip("\r\n")

                # skip comments or whitespace lines
                if re.match(r'^\s*(#|$)', line):
                    continue

                # it's a category
                m = re.match(r'^>(.*)$', line)
                if m:
                    # create category entry
                    questions[m.group(1)] = list()
                    cur_category = m.group(1)
                    continue

                # convert fake new-lines into real ones
                line = re.sub(r'\\n', '\n', line)

                # it's a question
                questions[cur_category].append(line)

    except Exception as e:
        context = "Problem parsing the question file: {}".format(filename)
        raise QuestionParsingError(context) from e

    return questions

def import_csv_questions(file_names: list, category_names:list, output_file=config['BASE_DIR'] + "data/questions.json") -> None:
    if len(file_names) != len(category_names):
        raise(Exception(f"Error while importing CSV files: the length of the list file_names does not match the lenth "
                        f"of the dir output_files"))

    questions = {}
    for i, csv_file in enumerate(file_names):
        category_questions = []
        with open(csv_file, mode='r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            # skip the first row since we expect it to contain column names
            csv_reader.__next__()
            for row in csv_reader:
                values = tuple(row)
                # Ignore this (an empty line at the file will read as a column with no cells)
                if len(values) == 0:
                    continue

                # TODO: add unit test that checks that the file has 4 columns
                category_questions.append({
                    "question": values[3],
                    "correct_answer": values[2]
                })
            questions[category_names[i]] = category_questions

    with open(output_file, mode='w', encoding='utf-8') as output_file:
        output_file.write(json.dumps(questions))

def parse_gamefile(filename):
    """Parses a game file. A game file holds the categories that are going to be
        played in order.
       Returns a list of category strings and a final question dict
    """
    # TODO should drop the old format entirely?
    # if so we need to be able to express final question somehow
    categories = list()
    final = None
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.rstrip("\r\n")

                # match: final: [category] text
                m = re.match(r'final: \[([^]]+)\] (.*)$', line)
                if m:
                    final = {'category': m.group(1), 'question': m.group(2)}
                    continue

                categories.append(line)

    except Exception as e:
        context = "Problem parsing the game file: {}".format(filename)
        raise GamefileParsingError(context) from e

    return categories, final


def question_to_html(question_text):
    """Parses the questions from the Beopardy Game Board format"""
    question_text = html.escape(question_text)

    # Warning, we don't support nested line heading options
    # UTF-8 is just killed since everything is UTF-8 now
    if question_text.startswith('[utf8]'):
        question_text = question_text.lstrip('[utf8]')

    # Fixed width strings
    if question_text.startswith('[fixed]'):
        question_text = question_text.lstrip('[fixed]')
        question_text = "<tt>{}</tt>".format(question_text)

    # Parsing images
    m = re.search(r'^\[img:([^\]]*)\]$', question_text)
    if m:
        # TODO file names will have to be hard to guess if we go multi-client
        # TODO push style into CSS
        return '<img src="/static/game-media/{}" width="100%" style="max-height: 100%; max-width: 100%; object-fit: contain;">'.format(m.group(1))

    # Transform new lines into <br>
    question_text = re.sub(r'\n', '<br/>', question_text)

    return "<p>" + question_text + "</p>"


def list_roundfiles():
    """List available roundfiles in config's data directory"""

    _glob = config['BASE_DIR'] + 'data/*.round'
    # return file names only
    return [os.path.basename(_f) for _f in glob.glob(_glob)]


def parse_question_id(qid):
    """
    Parses a question id in the form category X question Y (cXqY) and 
    returns a tuple with category, question or None if it didn't work.
    """
    match = re.match("c([0-9]+)q([0-9]+)", qid)
    if match is None:
        raise InvalidQuestionId("Invalid Question Id: {}".format(qid))
    col, row = match.groups()
    return (col, row)


class InvalidQuestionId(Exception):
    pass


class QuestionParsingError(Exception):
    pass


class GamefileParsingError(Exception):
    pass
