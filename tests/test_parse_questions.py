import pytest
import random

from utils import parse_questions, import_csv_questions
from config import config
from copy import deepcopy

QUESTIONS_FILENAME = '.resources/test/questions.json'
IMPORT_CSV_FILENAMES = [f"{config['BASE_DIR']}data/import/fragen_buzzwords.csv",
                        f"{config['BASE_DIR']}data/import/fragen_infosec_basics.csv",
                        f"{config['BASE_DIR']}data/import/fragen_malware.csv",
                        f"{config['BASE_DIR']}data/import/fragen_q4.csv",
                        f"{config['BASE_DIR']}data/import/fragen_q5.csv",
                        ]
IMPORT_CATEGORY_NAMES = ["Buzzwords", "Infosec Basics", "Malware", "Category4", "Category5"]


class TestUtils(object):

    # TODO: turn these tests into proper integration tests using temporary files

    def test_parse_questions_normal(self):
        actual = parse_questions(config['BASE_DIR'] + config['QUESTIONS_FILENAME'])
        assert type(actual) is dict
        assert len(actual) > 0

        first_category = actual["Buzzwords"]
        buzzwords_questions = first_category[0]
        assert 'question' in buzzwords_questions
        assert 'correct_answer' in buzzwords_questions

    def test_import_csv_questions_mismatch_lists(self):
        too_short_category_list = list(IMPORT_CSV_FILENAMES)
        del too_short_category_list[len(too_short_category_list) - 1]

        def f():
            import_csv_questions(IMPORT_CSV_FILENAMES, too_short_category_list)

        with pytest.raises(Exception):
            f()

    def test_import_csv_questions_invalid_file_path(self):
        incorrect_file_names = deepcopy(IMPORT_CSV_FILENAMES)
        incorrect_file_names[-1] = incorrect_file_names[-1] + ".1337"
        category_names = deepcopy(IMPORT_CATEGORY_NAMES)

        def f():
            import_csv_questions(incorrect_file_names, category_names)

        with pytest.raises(FileNotFoundError):
            f()

    def test_import_csv_questions_empty_lists(self):
        import_csv_questions([], [])

    def test_import_csv_questions_normal(self):
        csv_file_names = deepcopy(IMPORT_CSV_FILENAMES)
        category_names = deepcopy(IMPORT_CATEGORY_NAMES)

        import_csv_questions(csv_file_names, category_names)

    def test_import_csv_questions_single_file(self):
        import_csv_questions([IMPORT_CSV_FILENAMES[0]], [IMPORT_CATEGORY_NAMES[0]])
