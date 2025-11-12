def api3_v3_validation(case_id, agent_response_date, agent_response_info):
    case_id = case_id
    agent_response_date = agent_response_date
    data_type_mappings1 = {
        'case_id': str,
        'agent_response_date': int, 
        'agent_response_info': list
    }
    data_type_mappings2 = {
        'extract_type': str,
        'extract_type_num': int,
        'gpt_output': str,
        'intent': str,
        'agent_response_kb': int
    }
    output = None
    if case_id is None or case_id == '':
        output = {
            "status": 400,
            "message": "(Validation Error)The case_id field is required and must be a string.",
            "output": None
        }
    for field, expected_type in data_type_mappings1.items():
        value = locals()[field]
        if not isinstance(value, expected_type):
            output = {
                "status": 400,
                "message": f"(Validation Error)The {field} field has an incorrect format. Please recheck the input data.",
                "output": None
            }
            break
        if field == 'agent_response_info':
            for agent_dict in agent_response_info:
                intent = agent_dict.get('intent')
                for field2, expected_type2 in data_type_mappings2.items():
                    value2 = agent_dict.get(field2)
                    if (intent != 'Technical Support') and (field2 == 'agent_response_kb'):
                        continue
                    if (not isinstance(value2, expected_type2)):
                        output = {
                            "status": 400,
                            "message": f"(Validation Error)The {field}.{field2} ({value2}) field has an incorrect format. Please recheck the input data.",
                            "output": None
                        }
                        break
                    if field2 == 'agent_response_kb':
                        if (intent == 'Technical Support') and (value2 is None or value2 <= 0):
                            output = {
                                "status": 400,
                                "message": f"(Validation Error)The {field}.{field2} ({value2}) field is required and must be a positive integer when intent is 'Technical Support'.",
                                "output": None
                            }
                            break
                        if (intent != 'Technical Support') and (value2 is not None and value2 <= 0):
                            output = {
                                "status": 400,
                                "message": f"(Validation Error)The {field}.{field2} ({value2}) field must be a positive integer if provided.",
                                "output": None
                            }
                            break
    return output
