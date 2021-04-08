"""
Defines baseclasses for comparers.

Note: Any callable object with the correct signature can be used as a comparer
function. We use classes for comparer functions that have configuration options.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import abc
from mitxgraders.baseclasses import ObjectWithSchema

class Comparer(ObjectWithSchema):
    """
    Comparers are callable objects used as comparer functions in FormulaGrader problems.
    Unlike standard comparer functions, Comparers can be passed options at instantiation.

    This class is abstract. Comparers should inherit from it.
    """

    @abc.abstractmethod
    def __call__(self, comparer_params_eval, student_eval, utils):
        """
        Compares student input evalution with expected evaluation.

        Arguments:
            `comparer_params_eval`: The `comparer_params` list, numerically evaluated
                according to variable and function sampling.
            `student_eval`: The student's input, numerically evaluated according to
                variable and function sampling.
            `utils`: a convenience object, same as for simple comparers.
        Returns:
            bool or results dict
        """

class CorrelatedComparer(Comparer):
    """
    CorrelatedComparer are callable objects used as comparer functions
    in FormulaGrader problems. Unlike standard comparer functions, CorrelatedComparer
    are given access to all parameter evaluations at once.

    For example, a comparer function that decides whether the student input is a
    nonzero constant multiple of the expected input would need to be a correlated
    comparer so that it can determine if there is a linear relationship between
    the student and expected samples.

    This class is abstract. Correlated Comparers should inherit from it.
    """

    @abc.abstractmethod
    def __call__(self, comparer_params_evals, student_evals, utils):
        """
        Compares student input evalutions with expected evaluations.

        Below, N is the number of samples used by a FormulaGrader problem.

        Arguments:
            `comparer_params_evals`: a nested list of evaluated comparer params,
                [params_evals_0, params_evals_1,..., params_evals_N]
            `student_evals`: a list of N student input numerical evaluations
            `utils`: a convenience object, same as for simple comparers.
        Returns:
            bool or results dict
        """
