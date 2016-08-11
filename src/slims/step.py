import logging
import threading
import traceback

from .flowrun import Status

logger = logging.getLogger('genohm.slims.step')


class Step(object):
    """The step class defines the step properties of a SLimsGate flow.

    Parameters:
    name -- name of the step
    action -- action done by the step
    async -- a boolean that give the asynchronicity of the step
             its default value is False
    hidden -- a boolean that says if the step needs to be hidden
              its default value is False
    input -- a list of input parameters
    output -- a list of output parameters
    """
    def __init__(self, name, action, async=False, hidden=False, input=[], output=[]):
        self.action = action
        self.name = name
        self.hidden = hidden
        self.input = input
        self.output = output
        self.async = async

    def to_dict(self, route_id):
        return {
            'hidden': self.hidden,
            'name': self.name,
            'input': {
                'parameters': self.input
            },
            'process': {
                'asynchronous': self.async,
                'route': route_id,
            },
            'output': {
                'parameters': self.output
            },
        }

    def execute(self, flow_run):
        try:
            flow_run.check_user_secret()
            if self.async:
                logger.info("Starting to run step %s asynchronously", self.name)
                return self._execute_async(flow_run)
            else:
                logger.info("Starting to run step %s synchronously", self.name)
                return self._execute_inner(flow_run)
        except Exception:
            flow_run.log(traceback.format_exc())
            flow_run.update_status(Status.FAILED)
            logger.info("Failed running step %s", self.name)
            raise StepExecutionException

    def _execute_async(self, flow_run):
        thr = threading.Thread(target=self._execute_inner, args=[flow_run])
        thr.start()

    def _execute_inner(self, flow_run):
        try:
            value = self.action(flow_run)
            flow_run.update_status(Status.DONE)
            logger.info("Done running step %s", self.name)
            return value
        except Exception:
            flow_run.log(traceback.format_exc())
            flow_run.update_status(Status.FAILED)
            logger.info("Failed running step %s", self.name)
            raise StepExecutionException


class StepExecutionException(Exception):
    pass


def _simple_input(name, label, type, **kwargs):
    values = {'name': name, 'label': label, 'type': type}
    values.update(kwargs)
    return values


def text_input(name, label, **kwargs):
    """Allows to have short text input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'STRING', **kwargs)


def single_choice_with_field_list_input(name, label, fieldelements, fieldtype=None,
                                        **kwargs):
    """Allows to have a single choice out of a list input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    fieldelements -- the list of elements in which the choice needs to be made, usually strings
    fieldtype -- the type of the field elements
                 its default value is None
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"
    Returns: a dictionnary containing all these elements
    """

    return _choice_with_field_list_input(name, label, "SINGLE_CHOICE", fieldelements, fieldtype, **kwargs)


def multiple_choice_with_field_list_input(name, label, fieldelements, fieldtype=None, **kwargs):
    """Allows to have a multiple choice out of a list input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    fieldelements -- the list of elements in which the choice needs to be made, usually strings
    fieldtype -- the type of the field elements
                 its default value is None
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"
    Returns: a dictionnary containing all these elements
    """
    return _choice_with_field_list_input(name, label, "MULTIPLE_CHOICE", fieldelements, fieldtype, **kwargs)


def _choice_with_field_list_input(name, label, datatype, fieldelements, fieldtype=None, **kwargs):
    entries = []
    i = 0
    for fieldelement in fieldelements:
        field = {}
        if fieldtype is not None:
            field['type'] = fieldtype[i]
        else:
            field['type'] = None
        field['field'] = fieldelements[i]
        entries.append(field)
        i = i + 1

    values = {
        'name': name,
        'label': label,
        'type': datatype,
        'fieldList': {'entries': entries}
    }
    values.update(kwargs)
    return values


def single_choice_with_value_map_input(name, label, table=None, filtered=None,
                                       reference=None, fixed_choice_customer_field=None,
                                       **kwargs):
    """Allows to have a single choice out of a list input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    table -- the table of the possible choices to display
             its default value is None
    filtered -- the filter applied on the list of displayed choice
                its default value is None
    reference -- the name of the valueMap of the output of the previous step_dicts
                 its default value is None
    fixed_choice_customer_field -- the name of a customer field
                                   its default value is None
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"
    Returns: a dictionnary containing all these elements
    """

    return _choice_with_value_map_input(
        name, label, "SINGLE_CHOICE", table, filtered, reference, fixed_choice_customer_field, *kwargs)


def multiple_choice_with_value_map_input(name, label, table=None, filtered=None,
                                         reference=None, fixed_choice_customer_field=None,
                                         **kwargs):
    """Allows to have a multiple choice out of a list input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    table -- the table of the possible choices to display
             its default value is None
    filtered -- the filter applied on the list of displayed choice
                its default value is None
    reference -- the name of the valueMap of the output of the previous step_dicts
                 its default value is None
    fixed_choice_customer_field -- the name of a customer field
                                   its default value is None
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"
    Returns: a dictionnary containing all these elements
    """
    return _choice_with_value_map_input(
        name, label, "MULTIPLE_CHOICE", table, filtered, reference, fixed_choice_customer_field, *kwargs)


def _choice_with_value_map_input(name,
                                 label,
                                 datatype,
                                 table,
                                 filtered,
                                 reference,
                                 fixed_choice_customer_field,
                                 **kwargs):
    value_map = {
        'filter': filtered,
        'reference': reference,
        'table': table,
        'fixedChoiceCustomField': fixed_choice_customer_field
    }
    values = {
        'name': name,
        'label': label,
        'type': datatype,
        'valueMap': value_map
    }
    values.update(kwargs)
    return values


def date_input(name, label, **kwargs):
    """Allows to havea date input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'DATE', **kwargs)


def date_time_input(name, label, **kwargs):
    """Allows to have a date and time input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'DATETIME', **kwargs)


def time_input(name, label, **kwargs):
    """Allows to have a time input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'TIME', **kwargs)


def boolean_input(name, label, **kwargs):
    """Allows to have a yes or no choice input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'BOOLEAN', **kwargs)


def rich_text_input(name, label, **kwargs):
    """Allows to have rich text input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'TEXT', **kwargs)


def integer_input(name, label, **kwargs):
    """Allows to have integer input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'INTEGER', **kwargs)


def float_input(name, label, **kwargs):
    """Allows to have float input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'FLOAT', **kwargs)


def password_input(name, label, **kwargs):
    """Allows to have a password input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, 'PASSWORD', **kwargs)


def table_input(name, label, subparameters, **kwargs):
    """Allows to have a table input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    subparameters -- the list of paramteres that need to be in the table
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    values = {'name': name, 'label': label, 'type': "TABLE", 'subParameters': subparameters}
    values.update(kwargs)
    return values


# Message display by SLims
# File input and output together are currently not supported
def file_input(name, label, **kwargs):
    """Allows to have a file input for SLimsGate.

    Parameters:
    name -- the name of the input
    label -- the label of the input
    **kwargs -- every additional and optional parameter
                it needs to be of the form defaultValue="it is a default value"

    Returns: a dictionnary containing all these elements
    """
    return _simple_input(name, label, "FILE", **kwargs)


def file_output():
    """Allows to have a file output for SLimsGate.

    Returns: a dictionnary
    """
    return {'name': 'file', 'type': 'FILE'}


def value_map_output(name, datatype):
    """Allows to have a value map output for SLimsGate.

    Parameters:
    name -- the name of the output
    datatype -- the label of the output

    Returns: a dictionnary containing all these elements
    """
    return {'name': name, 'datatype': datatype, 'type': 'VALUEMAP'}
