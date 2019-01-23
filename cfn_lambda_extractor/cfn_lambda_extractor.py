import logging
import os
import re

def load_input_file(filename):
    logging.info("Loading input from file '{}'.".format(filename))
    k = os.path.basename(filename).split(".")[0]
    i = open(filename, "r")
    input_file_data = i.read()
    i.close()

    return input_file_data

def count_leading_spaces(line):
    return len(line) - len(line.lstrip(' '))

def start_zip_block(line):
    return line.lstrip().startswith("ZipFile:")

def valid_code(line):
    if line.lstrip().startswith("-"):
        return False

    return True

def replace_values_in_line(line, values):
    regex = re.match( r'^(.*)\${(.*?)}(.*)$', line)

    # If the line does not include any values, return
    if regex == None:
        return line

    value_name = regex.group(2)
    val = values.get(value_name, "UNKNOWN")
    logging.info("Replacing cfn value '{}' with '{}'.".format(value_name, val))

    # !! Currently asssumes all values are strings !!
    modified_line = regex.group(1) + str(val) + regex.group(3)

    # Recur until no more variables match
    return replace_values_in_line(modified_line, values)

def replace_values(code, values):
    updated_code = {}
    for fn_name, fn_code in code.items():
        updated_code[fn_name] = [replace_values_in_line(l, values) for l in fn_code]
    return updated_code

def format_python_code(code):
    modified_code = {}
    for k, v in code.items():
        if len(v) == 0:
            logging.debug("Removing empty function '{}'.".format(k))
            continue

        logging.debug("Formatting function '{}'.".format(k))
        modified_fn = []

        num_spaces_function_indented = count_leading_spaces(v[0])
        logging.debug("Function indented {} spaces.".format(num_spaces_function_indented))

        logging.debug("Removing leading {} from every line.".format(num_spaces_function_indented))
        modified_code[k] = [line[num_spaces_function_indented:] for line in v]
    return modified_code

def load_functions_from_resource_data(resource_data):
    in_function_body = False
    significant_white_space = 0

    code = {}
    count = 0
    for line in resource_data:
        if start_zip_block(line) and not in_function_body:
            logging.debug("Found line starting ZipFile block. Starting new function: {}".format(line))
            in_function_body = True
            significant_white_space = count_leading_spaces(line)
            code[str(count)] = []
            continue

        if in_function_body and valid_code(line) == False:
            logging.debug("Not valid code. Continuing: {}".format(line))
            continue

        if in_function_body and (significant_white_space <= count_leading_spaces(line) or line == ""):
            logging.debug("In Lambda body, valid code, appending line to function: {}".format(line))
            code[str(count)].append(line)
            continue

        if in_function_body:
            logging.debug("End of function, setting in function body to false and incrementing function count: {}".format(line))
            count += 1
            significant_white_space = 0
            in_function_body = False

        logging.debug("Ignoring line: {}".format(line))

    logging.info("Loaded {} function(s).".format(len(code)))

    return code

def load_resources(cfn_data):
    result = []
    in_resources = False
    for line in cfn_data.split("\n"):
        if line.startswith("Resources"):
            logging.debug("Found line starting Resources block")
            in_resources = True
            continue

        if count_leading_spaces(line) == 0 and line != "":
            in_resources = False
            continue

        if in_resources:
            result.append(line)

    return result

def convert_fns_to_str(fns):
    return {k: "\n".join(v) for (k, v) in fns.items()}

def extract_functions(cfn_data, values, convert_cfn_variables=True):
    resource_data = load_resources(cfn_data)
    fns = load_functions_from_resource_data(resource_data)
    modified_fns = format_python_code(fns)
    replaced_values = replace_values(modified_fns, values)
    return convert_fns_to_str(replaced_values)

def parse_csv_input_values(input_values):
    logging.debug("Paring input '{}'.".format(input_values))
    result = {}

    if input_values != "":
        result = {x[0]: x[1] for x in [v.split("=") for v in input_values.split(",")]}

    logging.debug("Parsed following values '{}'.".format(result))
    return result
