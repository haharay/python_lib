"""
sampling.py

Contains classes for sampling numerical values:
* RealInterval
* IntegerRange
* DiscreteSet
* ComplexRectangle
* ComplexSector
* DependentSampler

and for specifying functions:
* SpecificFunctions
* RandomFunction

Contains some helper functions used in grading formulae:
* gen_symbols_samples
* construct_functions
* construct_constants
* construct_suffixes

All of these classes perform random sampling. To obtain a sample, use class.gen_sample()
"""
from __future__ import print_function, division, absolute_import, unicode_literals

from numbers import Number
import abc
import random
import six
import numpy as np
from voluptuous import Schema, Required, All, Coerce, Any, Extra
from mitxgraders.baseclasses import ObjectWithSchema
from mitxgraders.exceptions import ConfigError
from mitxgraders.helpers.validatorfuncs import (
    Positive, NumberRange, ListOfType, TupleOfType, is_callable,
    has_keys_of_type, text_string, Nullable)
from mitxgraders.helpers.compatibility import coerce_string_keys_to_text_type
from mitxgraders.helpers.calc import (
    METRIC_SUFFIXES, CalcError, evaluator, parse, MathArray)

# Set the objects to be imported from this grader
__all__ = [
    "RealInterval",
    "IntegerRange",
    "DiscreteSet",
    "ComplexRectangle",
    "ComplexSector",
    "SpecificFunctions",
    "RandomFunction",
    "DependentSampler"
]

def set_seed(seed=None):
    random.seed(seed)
    np.random.seed(seed)

class AbstractSamplingSet(ObjectWithSchema):  # pylint: disable=abstract-method
    """
    Represents a set from which random samples are taken.

    Note that this is an abstract class.
    """

    @abc.abstractmethod
    def gen_sample(self):
        """Generate a sample from this sampling set"""


class VariableSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """
    Represents a set from which random variable samples are taken.

    Note that this is an abstract class.
    """


class ScalarSamplingSet(VariableSamplingSet):  # pylint: disable=abstract-method
    """
    Represents a set from which random scalar variable samples are taken.

    Note that this is an abstract class.
    """


class FunctionSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """
    Represents a set from which random function samples are taken.

    Note that this is an abstract class.
    """


class RealInterval(ScalarSamplingSet):
    """
    Represents an interval of real numbers from which to sample.

    Config:
        start (float): Lower end of the range (default 1)
        stop (float): Upper end of the range (default 5)

    Usage
    =====
    Generate random floats betweens -2 and 4
    >>> ri = RealInterval(start=-2, stop=4)

    You can also initialize with an interval as a list:
    >>> ri = RealInterval([-2,4])
    """
    schema_config = NumberRange()

    def __init__(self, config=None, **kwargs):
        """
        Validate the specified configuration.
        First apply the voluptuous validation.
        Then ensure that the start and stop are the right way around.
        """
        super(RealInterval, self).__init__(config, **kwargs)
        if self.config['start'] > self.config['stop']:
            self.config['start'], self.config['stop'] = self.config['stop'], self.config['start']

    def gen_sample(self):
        """Returns a random real number in the range [start, stop]"""
        start, stop = self.config['start'], self.config['stop']
        return start + (stop - start) * np.random.random_sample()


class IntegerRange(ScalarSamplingSet):
    """
    Represents an interval of integers from which to sample.

    Config:
        start (int): Lower end of the range (default 1)
        stop (int): Upper end of the range (default 5)

    Both start and stop are included in the interval.

    Usage
    =====
    Generate random integers betweens -2 and 4
    >>> integer = IntegerRange(start=-2, stop=4)

    You can also initialize with an interval:
    >>> integer = IntegerRange([-2,4])
    """
    schema_config = NumberRange(int)

    def __init__(self, config=None, **kwargs):
        """
        Validate the specified configuration.
        First apply the voluptuous validation.
        Then ensure that the start and stop are the right way around.
        """
        super(IntegerRange, self).__init__(config, **kwargs)
        if self.config['start'] > self.config['stop']:
            self.config['start'], self.config['stop'] = self.config['stop'], self.config['start']

    def gen_sample(self):
        """Returns a random integer in range(start, stop)"""
        return np.random.randint(low=self.config['start'], high=self.config['stop'] + 1)


class ComplexRectangle(ScalarSamplingSet):
    """
    Represents a rectangle in the complex plane from which to sample.

    Config:
        re (list): Range for the real component (default [1,3])
        im (list): Range for the imaginary component (default [1,3])

    Usage
    =====
    >>> rect = ComplexRectangle(re=[1,4], im=[-5,0])
    """
    schema_config = Schema({
        Required('re', default=[1, 3]): NumberRange(),
        Required('im', default=[1, 3]): NumberRange()
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set up the real and imaginary
        parts as RealInterval objects
        """
        super(ComplexRectangle, self).__init__(config, **kwargs)
        self.re = RealInterval(self.config['re'])
        self.im = RealInterval(self.config['im'])

    def gen_sample(self):
        """Generates a random sample in the defined rectangle in the complex plane"""
        return self.re.gen_sample() + self.im.gen_sample()*1j


class ComplexSector(ScalarSamplingSet):
    """
    Represents an annular sector in the complex plane from which to sample,
    based on a given range of modulus and argument.

    Config:
        modulus (list): Range for the modulus (default [1,3])
        argument (list): Range for the argument (default [0,pi/2])

    Usage
    =====
    Sample from the unit circle
    >>> sect = ComplexSector(modulus=[0,1], argument=[-np.pi,np.pi])
    """
    schema_config = Schema({
        Required('modulus', default=[1, 3]): NumberRange(),
        Required('argument', default=[0, np.pi/2]): NumberRange()
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set up the modulus and argument
        parts as RealInterval objects
        """
        super(ComplexSector, self).__init__(config, **kwargs)
        self.modulus = RealInterval(self.config['modulus'])
        self.argument = RealInterval(self.config['argument'])

    def gen_sample(self):
        """Generates a random sample in the defined annular sector in the complex plane"""
        return self.modulus.gen_sample() * np.exp(1j * self.argument.gen_sample())


class DiscreteSet(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a discrete set of values from which to sample, which may consist of numbers
    and/or MathArrays.

    Initialize with a single value or a non-empty tuple of values. Note that we use
    a tuple instead of a list so that the range [0,1] isn't confused with the set (0, 1).
    The set of values can include numbers and MathArrays.

    Historical note: When we first implemented this, voluptuous didn't work with sets, and
    so we used tuples instead. Now we can't change to sets without breaking backwards
    compatability, alas.

    Usage
    =====
    Specify a single value (note that you would usually use a user_constant for this)
    >>> values = DiscreteSet(3.142)
    >>> values.gen_sample() == 3.142
    True

    Specify a tuple of values
    >>> values = DiscreteSet((1,3,5,7,9))

    Specify an array
    >>> ident = MathArray([[1, 0], [0, 1]])
    >>> values = DiscreteSet(ident)

    Specify a set of arrays
    >>> myarray = MathArray([[1, 2], [3, 4]])
    >>> values = DiscreteSet((ident, myarray))

    Specify a mixed set
    >>> values = DiscreteSet((1, ident))

    """

    # Take in an individual or tuple of numbers/MathArrays
    schema_config = Schema(TupleOfType((Number, MathArray)))

    def gen_sample(self):
        """Return a random entry from the given set"""
        return random.choice(self.config)


class RandomFunction(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Generates a random well-behaved function on demand.

    Currently implemented as a sum of trigonometric functions with random amplitude,
    frequency and phase. You can control the center and amplitude of the resulting
    oscillations by specifying center and amplitude. The complex flag allows you to
    generate complex random functions.

    Config:
        input_dim (int): Number of input arguments. 1 is a unary function (default 1)
        output_dim (int): Number of output dimensions. 1 = scalar, more than 1 is a vector
            (default 1)
        num_terms (int): Number of random sinusoid terms to add together (default 3)
        center (float): Center around which oscillations occur (default 0)
        amplitude (float): Maximum amplitude of the function (default 10)
        complex (bool): Generate a complex random function (default False)

    Usage
    =====
    Generate a random continous function
    >>> funcs = RandomFunction()

    By default, the generated functions are R-->R. You can specify the
    input and output dimensions:
    >>> funcs = RandomFunction(input_dim=3, output_dim=2)

    To control the range of the function, specify a center and amplitude. The bounds of
    the function will be center - amplitude < func(x) < center + amplitude.
    The following will give oscillations between 0 and 1.
    >>> funcs = RandomFunction(center=0.5, amplitude=0.5)
    """

    schema_config = Schema({
        Required('input_dim', default=1): Positive(int),
        Required('output_dim', default=1): Positive(int),
        Required('num_terms', default=3): Positive(int),
        Required('center', default=0): Number,
        Required('amplitude', default=10): Positive(Number),
        Required('complex', default=False): bool
    })

    def gen_sample(self):
        """
        Returns a randomly chosen 'nice' function.

        The output is a vector with output_dim dimensions:
        Y^i = sum_{jk} A^i_{jk} sin(B^i_{jk} X_k + C^i_{jk})

        i ranges from 1 to output_dim
        j ranges from 1 to num_terms
        k ranges from 1 to input_dim
        """
        # Generate arrays of random values for A, B and C
        output_dim = self.config['output_dim']
        input_dim = self.config['input_dim']
        num_terms = self.config['num_terms']
        # Amplitudes A range from 0.5 to 1
        A = np.random.rand(output_dim, num_terms, input_dim) / 2 + 0.5
        # If we're complex, multiply the amplitude by a complex phase
        if self.config['complex']:
            complexphases = np.random.rand(output_dim, num_terms, input_dim) * np.pi * 2j
            A = A * np.exp(complexphases)
        # Angular frequencies B range from -pi to pi
        B = 2 * np.pi * (np.random.rand(output_dim, num_terms, input_dim) - 0.5)
        # Phases C range from 0 to 2*pi
        C = 2 * np.pi * np.random.rand(output_dim, num_terms, input_dim)

        def random_function(*args):
            """Function that generates the random values"""
            # Check that the dimensions are correct
            if len(args) != input_dim:
                msg = "Expected {} arguments, but received {}".format(input_dim, len(args))
                raise ConfigError(msg)

            # Turn the inputs into an array
            xvec = np.array(args)
            # Repeat it into the shape of A, B and C
            xarray = np.tile(xvec, (output_dim, num_terms, 1))
            # Compute the output matrix
            output = A * np.sin(B * xarray + C)
            # Sum over the j and k terms
            # We have an old version of numpy going here, so we can't use
            # fullsum = np.sum(output, axis=(1, 2))
            fullsum = np.sum(np.sum(output, axis=2), axis=1)

            # Scale and translate to fit within center and amplitude
            fullsum = fullsum * self.config["amplitude"] / self.config["num_terms"]
            fullsum += self.config["center"]

            # Return the result
            return MathArray(fullsum) if output_dim > 1 else fullsum[0]

        # Tag the function with the number of required arguments
        random_function.nin = input_dim

        return random_function


class SpecificFunctions(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a set of user-defined functions for use in a grader, one of which will
    be randomly selected. A single function can be provided here, but this is intended
    for lists of functions to be randomly sampled from.

    Initialize with either a single function, or a list of functions.

    Usage
    =====
    Initialize with a specific function.
    >>> step_func = lambda x : 0 if x<0 else 1
    >>> functions = SpecificFunctions(step_func)

    Initialize with a list of functions.
    >>> functions = SpecificFunctions([np.sin, np.cos, np.tan])
    """

    # Take in a function or list of callable objects
    schema_config = Schema(ListOfType(object, is_callable))

    def gen_sample(self):
        """Return a random entry from the given list"""
        return random.choice(self.config)


class DependentSampler(VariableSamplingSet):
    """
    Represents a variable that depends on other variables.

    You must initialize with the list of variables this depends on as well as the formula
    for this variable. Note that only base formulas and suffixes are available for this
    computation.

    Usage
    =====
    Specify a single value
    >>> ds = DependentSampler(depends=['x', 'y', 'z'], formula="sqrt(x^2+y^2+z^2)")
    """

    # Take in an individual or tuple of numbers
    schema_config = Schema({
        Required('depends', default=None): Nullable([text_string]),
        Required('formula'): text_string
    })

    def __init__(self, config=None, **kwargs):
        """Perform initialization"""
        super(DependentSampler, self).__init__(config, **kwargs)

        # Construct the 'depends' list (overwrites whatever was provided, as this does it better!)
        try:
            parsed = parse(self.config['formula'])
            self.config['depends'] = list(parsed.variables_used)
        except CalcError:
            raise ConfigError("Formula error in dependent sampling formula: " +
                              self.config["formula"])

    def gen_sample(self):
        """Return a random entry from the given set"""
        raise Exception("DependentSampler must be invoked with compute_sample.")

    def compute_sample(self, sample_dict, functions, suffixes):
        """Compute the value of this sample"""
        try:
            result, _ = evaluator(formula=self.config['formula'],
                                  variables=sample_dict,
                                  functions=functions,
                                  suffixes=suffixes)
        except CalcError:
            raise ConfigError("Formula error in dependent sampling formula: " +
                              self.config["formula"])

        return result

def is_subset(iterable, iterable_superset):
    """
    Helper function for gen_symbols_samples below.
    Checks to see if every item in iterable is in iterable_superset.
    """
    for item in iterable:
        if item not in iterable_superset:
            return False
    return True

def gen_symbols_samples(symbols, samples, sample_from, functions, suffixes, constants):
    """
    Generates a list of dictionaries mapping symbol names to values.

    Arguments:
        symbols ([str]): a list of symbol names
        samples (int): how many samples to generate
        sample_from: a dictionary mapping symbol names to sampling sets
        functions (dict): function-scope for evaluating dependent variables
        suffixes (dict): suffix-scope for evaluating dependent variables

    The symbols argument will usually be config['variables']
    or config['functions'].

    Usage
    =====
    >>> variable_samples = gen_symbols_samples(
    ...     ['a', 'b'],
    ...     3,
    ...     {
    ...         'a': RealInterval([1,3]),
    ...         'b': RealInterval([-4,-2])
    ...     }, {}, {}, {}
    ... )
    >>> variable_samples # doctest: +SKIP
    [
        {'a': 1.4765130193614819, 'b': -2.5596368656227217},
        {'a': 2.3141937628942406, 'b': -2.8190938526155582},
        {'a': 2.8169225565573566, 'b': -2.6547771579673363}
    ]
    """
    # Separate independent and dependent symbols
    independent = [
        symbol for symbol in symbols
        if not isinstance(sample_from[symbol], DependentSampler)
    ]

    pruned_constants = {sym: constants[sym] for sym in constants if sym not in symbols}

    # Generate the samples
    sample_list = []
    for _ in range(samples):
        # Generate independent samples
        sample_dict = pruned_constants.copy()
        sample_dict.update({
            symbol: sample_from[symbol].gen_sample() for symbol in independent
        })

        # Generate dependent samples, following chains as necessary
        unevaluated_dependents = {
            symbol: sample_from[symbol].config['depends'] for symbol in symbols
            if isinstance(sample_from[symbol], DependentSampler)
        }
        while unevaluated_dependents:
            progress_made = False
            for symbol, dependencies in list(unevaluated_dependents.items()):
                if is_subset(dependencies, sample_dict):
                    sample_dict[symbol] = sample_from[symbol].compute_sample(
                        sample_dict, functions, suffixes)
                    del unevaluated_dependents[symbol]
                    progress_made = True

            if not progress_made:
                # Two possible causes
                # 1: Depends on variables that are undefined
                # Check for this first
                all_depends = set()
                for symbol, dependencies in list(unevaluated_dependents.items()):
                    for item in dependencies:
                        all_depends.add(item)
                bad_items = []
                for item in all_depends:
                    if item not in unevaluated_dependents and item not in sample_dict:
                        bad_items.append(item)
                if bad_items:
                    bad_symbols = ", ".join(sorted(bad_items))
                    raise ConfigError("DependentSamplers depend on undefined quantities: " +
                                      bad_symbols)

                # 2: Circular dependencies
                bad_symbols = ", ".join(sorted(unevaluated_dependents.keys()))
                raise ConfigError("Circularly dependent DependentSamplers detected: " +
                                  bad_symbols)

        sample_list.append(sample_dict)
    return sample_list

# Used by NumericalGrader
schema_user_functions_no_random = All(
    has_keys_of_type(six.string_types),
    coerce_string_keys_to_text_type,
    {Extra: is_callable}
)
# Used by FormulaGrader and friends
schema_user_functions = All(
    has_keys_of_type(six.string_types),
    coerce_string_keys_to_text_type,
    {Extra: Any(is_callable,
                All([is_callable], Coerce(SpecificFunctions)),
                FunctionSamplingSet)},
)

def construct_functions(default_functions, user_funcs):
    """
    Constructs functions for use in sampling math expressions.

    Arguments:
        default_funcs: a dict mapping function names (strings) to functions
        user_funcs: a dict mapping function names (strings) to functions OR
            FunctionSamplingSet instances

    Returns:
        a tuple (functions, random_functions) of dictionaries:
        functions: maps function names to functions
        random_functions: maps function names to function sampling sets

    Usage
    =====
    Sorts user_funcs into functions and FunctionSamplingSet instances,
    merging the normal functions into a copy of default_funcs:
    >>> from math import sin, cos, tan
    >>> default_funcs = {'sin': sin, 'cos': cos}
    >>> func, random_func = tan, RandomFunction()
    >>> user_funcs = {
    ...     'tan': func,
    ...     'f': random_func
    ... }
    >>> funcs, random_funcs = construct_functions(default_funcs, user_funcs)
    >>> funcs == {'sin': sin, 'cos': cos, 'tan': tan} # contains defaults and tan
    True
    >>> random_funcs == {'f': random_func}
    True

    Does not mutate default_funcs:
    >>> default_funcs == {'sin': sin, 'cos': cos}
    True
    """
    funcs = default_functions.copy()
    random_funcs = {}
    for f in user_funcs:
        # Check if we have a random function or a normal function
        if isinstance(user_funcs[f], FunctionSamplingSet):
            random_funcs[f] = user_funcs[f]
        else:
            # f is a normal function
            funcs[f] = user_funcs[f]

    return funcs, random_funcs

def validate_user_constants(*allow_types):
    return All(
            has_keys_of_type(six.string_types),
            coerce_string_keys_to_text_type,
            {Extra: Any(Any(*allow_types), None)}
    )

def construct_constants(default_variables, user_consts):
    """
    Create a new dict that is the merge of user_consts into default_variables

    Usage
    =====
    >>> default_variables = {
    ...     'i': 1j,
    ...     'pi': 3.141592653589793,
    ...     'e': 2.718281828459045,
    ...     'j': 1j
    ... }
    >>> construct_constants(default_variables, {}) == default_variables
    True

    >>> construct_constants(default_variables, {"T": 1.5}) == {
    ...     'i': 1j,
    ...     'pi': 3.141592653589793,
    ...     'e': 2.718281828459045,
    ...     'T': 1.5, 'j': 1j
    ... }
    True

    """
    constants = default_variables.copy()

    # Add in any user constants
    for var in user_consts:
        constants[var] = user_consts[var]

    return constants

def construct_suffixes(default_suffixes, metric=False):
    """
    Returns a copy of default_suffixes. If metric=True, metric suffixes
    are merged into the copy.

    Usage
    =====
    >>> default_suffixes={'%': 0.01}
    >>> construct_suffixes(default_suffixes) == {'%': 0.01}
    True

    >>> suff = construct_suffixes(default_suffixes, metric=True)
    >>> suff['G'] == 1e9
    True
    """
    suffixes = default_suffixes.copy()
    if metric:
        suffixes.update(METRIC_SUFFIXES)
    return suffixes
