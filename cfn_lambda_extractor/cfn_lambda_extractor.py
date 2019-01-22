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

def replace_values_in_function(fn_code, values):
    updated_fn = []
    for line in fn_code:
        regex = re.match( r'^(.*)\${(.*?)}(.*)$', line)

        if regex == None:
            updated_fn.append(line)
            continue

        value_name = regex.group(2)
        val = values.get(value_name, "UNKNOWN")
        logging.info("Replacing cfn value '{}' with '{}'.".format(value_name, val))
        l = regex.group(1) + str(val) + regex.group(3) # !! Currently asssumes all values are strings !!
        updated_fn.append(l)

    return updated_fn

def replace_values(code, values):
    updated_code = {}
    for fn_name, fn_code in code.items():
        updated_code[fn_name] = replace_values_in_function(fn_code, values)
    return updated_code

def format_python_code(code):
    modified_code = {}
    for k, v in code.items():
        if len(v) == 0:
            logging.debug("Removing empty function '{}'.".format(k))
            continue

        logging.debug("Formatting function '{}'.".format(k))
        modified_fn = []
        l = count_leading_spaces(v[0])
        for line in v:
            x = line[l:]
            modified_fn.append(x)
        modified_code[k] = modified_fn
    return modified_code

def load_functions(resource_data):
    in_zip_file = False
    significant_white_space = 0

    code = {}
    count = 0
    for line in resource_data:
        logging.debug("Starting processing line: {}".format(line))

        if start_zip_block(line):
            logging.debug("Found line starting ZipFile block")
            in_zip_file = True
            significant_white_space = count_leading_spaces(line)
            code[str(count)] = []
            continue

        if in_zip_file and valid_code(line) == False:
            logging.debug("Not valid code.")
            continue

        if in_zip_file and (significant_white_space <= count_leading_spaces(line) or line == ""):
            logging.debug("Appending line to function.")
            code[str(count)].append(line)
            continue

        if in_zip_file:
            logging.debug("End of function, Incremeding function count.")
            count += 1
            significant_white_space = 0
            in_zip_file = False

        logging.debug("Ignoring line.")

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
    r = {}
    for k, v in fns.items():
        r[k] = "\n".join(v)
    return r

def extract_functions(cfn_data, values, convert_cfn_variables=True):
    resource_data = load_resources(cfn_data)
    fns = load_functions(resource_data)
    modified_fns = format_python_code(fns)
    replaced_values = replace_values(modified_fns, values)
    return convert_fns_to_str(replaced_values)

def parse_csv_input_values(input_values):
    result = {}

    if input_values == "":
        return result

    x = [v.split("=") for v in input_values.split(",")]
    y = [{v[0]: v[1]} for v in x]
    [result.update(pair) for pair in y]
    logging.debug("Parsed following values '{}'.".format(result))
    return result
