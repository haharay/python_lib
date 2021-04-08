"""
intervalgrader.py

Grader for intervals consisting of two formula entries, as well
as enclosing brackets.
"""
from __future__ import print_function, division, absolute_import, unicode_literals

import six

from voluptuous import Required, Schema, Any, All, Length

from mitxgraders.baseclasses import AbstractGrader
from mitxgraders.stringgrader import StringGrader
from mitxgraders.listgrader import SingleListGrader, demand_no_empty
from mitxgraders.formulagrader.formulagrader import FormulaGrader, NumericalGrader
from mitxgraders.exceptions import ConfigError, InvalidInput, MissingInput
from mitxgraders.helpers.validatorfuncs import text_string

class IntervalGrader(SingleListGrader):
    """
    IntervalGrader grades a pair of numbers describing an interval.
    Both the interval bracketing and the numbers are graded.
    The following are examples of possible entries:
    * [1, 2)
    * [0, 1+pi]
    By default, available brackets are [] and (), but other options are available through
    configuration (e.g., <> and {}).

    Answers can be provided in one of three ways:
    * Inferred through the 'expect' keyword
    * Supplied as a string
    * Entered as a list of four entries:
        - Open bracket
        - Lower bound
        - Upper bound
        - Closing bracket
    The second method can use all of the ItemGrader answer description functionality on
    the answer as a whole, while the third can additionally apply the functionality to
    each component of the answer.

    Grading works by first grading the entries. If the entries are awarded credit, then
    that credit may be modified by the grading of the brackets. (So, when a grade_decimal
    is specified for both the bracket and the bound, the two are multiplied together.)
    When partial credit is turned on, each half of the interval is worth 50% of the overall
    credit.

    No credit is awarded for getting the entries backwards.

    Warning: If the formula you're typing in uses a function that has more than one argument
    (or for whatever reason uses a comma), you should change the delimiter from a comma to
    something else.

    Warning: If using MJxPrep.js to format answers nicely, you will probably want to turn
    off column vectors. Otherwise, "[1, 2]" will display as a vector rather than as an interval.

    Configuration options:
        opening_brackets (str): A string of allowed opening bracket characters (default '[(')

        closing_brackets (str): A string of allowed closing bracket characters (default '])')

        delimiter (str): Single character to use as the separator between entries (default ',')

        subgrader (FormulaGrader or NumericalGrader): The grader to use to grade each individual
            entry (default NumericalGrader(tolerance=1e-13, allow_inf=True))

        partial_credit (bool): Whether to award partial credit for a partly-correct answer
            (default True)
    """

    @property
    def schema_config(self):
        """Define the configuration options for IntervalGrader"""
        # Construct the default SingleListGrader schema
        schema = super(IntervalGrader, self).schema_config
        # Append options
        return schema.extend({
            # Hardcode some SingleListGrader options
            Required('ordered', default=True): True,
            Required('length_error', default=True): True,
            Required('missing_error', default=True): True,

            # Subgrader default is set to NumericalGrader(tolerance=1e-13, allow_inf=True)
            # in initialization
            Required('subgrader', default=None): Any(FormulaGrader, None),
            Required('opening_brackets', default='[('): All(text_string, Length(min=1)),
            Required('closing_brackets', default='])'): All(text_string, Length(min=1))
        })

    def __init__(self, config=None, **kwargs):
        """
        Validate the IntervalGrader's configuration.
        """
        # Step 1: Provide the default subgrader
        use_config = config if config else kwargs
        if use_config.get('subgrader') is None:
            use_config['subgrader'] = NumericalGrader(tolerance=1e-13, allow_inf=True)

        # Step 2: Validate the configuration using SingleListGrader routines
        super(IntervalGrader, self).__init__(use_config)

    def post_schema_ans_val(self, answer_tuple):
        """
        Used to validate the individual 'expect' lists in the 'answers' key.
        This must be done after the schema has finished validation, as we need access
        to the 'subgraders' configuration key to perform this validation.
        """
        # The structure of answer_tuple at this stage is:
        # tuple(dict('expect', 'grade_decimal', 'ok', 'msg'))
        # where 'expect' is a list that needs validation.

        # If 'expect' is a string, use infer_from_expect to convert it to a list.
        for entry in answer_tuple:
            if isinstance(entry['expect'], six.string_types):
                entry['expect'] = self.infer_from_expect(entry['expect'])

        # Assert that all answers have length 4
        for answer_list in answer_tuple:
            if len(answer_list['expect']) != 4:
                raise ConfigError("Answer list must have 4 entries: opening bracket, lower bound, "
                                  "upper bound, closing bracket.")

        # Make sure that no entries are empty
        demand_no_empty(answer_tuple)

        # Validate the first and last entries (the brackets)
        # We use a StringGrader to run appropriate schema coercion
        grader = StringGrader()
        for answer_list in answer_tuple:
            expect = answer_list['expect']
            for index, answer in zip((0, 3), (expect[0], expect[3])):
                # Run the answers through the generic schema and post-schema validation
                expect[index] = grader.schema_answers(answer)
                expect[index] = grader.post_schema_ans_val(expect[index])

        # Validate the second and third entries (lower and upper limits)
        grader = self.config['subgrader']
        for answer_list in answer_tuple:
            expect = answer_list['expect']
            for index, answer in zip((1, 2), expect[1:3]):
                # Run the answers through the subgrader schema and the post-schema validation
                expect[index] = grader.schema_answers(answer)
                expect[index] = grader.post_schema_ans_val(expect[index])

        # Assert that the first and last entries are single characters that
        # exist in the opening_brackets and closing_brackets configuration options
        for answer_list in answer_tuple:
            # Opening brackets
            for entry in answer_list['expect'][0]:
                if len(entry['expect']) != 1:
                    raise ConfigError("Opening bracket must be a single character.")
                if entry['expect'] not in self.config['opening_brackets']:
                    raise ConfigError("Invalid opening bracket. The opening_brackets configuration allows for '"
                                      + "', '".join(char for char in self.config['opening_brackets'])
                                      + "' as opening brackets.")

            # Closing brackets
            for entry in answer_list['expect'][3]:
                if len(entry['expect']) != 1:
                    raise ConfigError("Closing bracket must be a single character.")
                if entry['expect'] not in self.config['closing_brackets']:
                    raise ConfigError("Invalid closing bracket. The closing_brackets configuration allows for '"
                                      + "', '".join(char for char in self.config['closing_brackets'])
                                      + "' as closing brackets.")

        return answer_tuple

    def infer_from_expect(self, expect):
        """
        Infer answers from the expect parameter. Returns the resulting answers key.

        Shadows the SingleListGrader infer_from_expect function.

        For example, we want to turn '[a, b)' -> ['[', 'a', 'b', ')'].
        """
        expect = expect.strip()
        # Check that the answer has at least 2 characters
        if len(expect) < 5:
            raise ConfigError('Unable to read interval from answer: "{}"'.format(expect))

        # Parse the middle bit using SingleListGrader
        middle = super(IntervalGrader, self).infer_from_expect(expect[1:-1])

        # Make a list: open_bracket, lower, upper, close_bracket
        answers = [expect[0]] + middle + [expect[-1]]
        return answers

    def check_response(self, answer, student_input, **kwargs):
        """Check student_input against a given answer list"""
        # Split the student response
        student_input = student_input.strip()
        if len(student_input) < 5:
            raise ConfigError('Unable to read interval from answer: "{}"'.format(student_input))
        s_opening = student_input[0]
        s_closing = student_input[-1]
        s_middle = student_input[1:-1]

        # Ensure that the opening and closing brackets are valid
        if s_opening not in self.config['opening_brackets']:
            raise InvalidInput("Invalid opening bracket: '{}'. Valid options are: '".format(s_opening)
                              + "', '".join(char for char in self.config['opening_brackets']) + "'.")
        if s_closing not in self.config['closing_brackets']:
            raise InvalidInput("Invalid closing bracket: '{}'. Valid options are: '".format(s_closing)
                              + "', '".join(char for char in self.config['closing_brackets']) + "'.")

        # Let SingleListGrader do the grading of the middle bit
        middle_answer = {
            'expect': answer['expect'][1:3],
            'ok': answer['ok'],
            'msg': answer['msg'],
            'grade_decimal': answer['grade_decimal']
        }
        result = super(IntervalGrader, self).check_response(middle_answer, s_middle, **kwargs)
        grade_list = result['individual']

        # Grade the opening bracket
        self.grade_bracket(answer['expect'][0], s_opening, grade_list[0])
        # Grade the closing bracket
        self.grade_bracket(answer['expect'][3], s_closing, grade_list[1])

        # Convert the grade list to a single return result
        return self.process_grade_list(grade_list, 2, answer['msg'], answer['grade_decimal'])

    def grade_bracket(self, answers, student_answer, grade_entry):
        """
        Grade a bracket, adding to the grade_entry as appropriate.
        """
        # If the number is wrong, the bracket doesn't need to be graded
        if grade_entry['grade_decimal'] == 0:
            return grade_entry

        # Find the bracket that awards the most credit (could be 0)
        best = None
        for bracket in answers:
            if student_answer == bracket['expect']:
                if best is None or bracket['grade_decimal'] > best['grade_decimal']:
                    best = bracket

        # If no answer was found, zero out the score
        if best is None:
            grade_entry['grade_decimal'] = 0
            grade_entry['ok'] = False
            return grade_entry

        # Update the grade_decimal and ok entries, as well as the message
        grade_entry['grade_decimal'] *= best['grade_decimal']
        if best['msg']:
            if grade_entry['msg']:
                grade_entry['msg'] += '\n'
            grade_entry['msg'] += best['msg']

        # Fix the ok entry
        grade_entry['ok'] = AbstractGrader.grade_decimal_to_ok(grade_entry['grade_decimal'])

        return grade_entry
