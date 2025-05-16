def test_group_docs(properties):
    import numpy as np
    expected_properties = {
        "defect_grouping_without_key_function": {
            "format": "str",
            "value": "N_i|N_i|v_Ga,v_Ga|v_N,v_N"
        },
        "defect_grouping_with_key_function": {
            "format": "str",
            "value": "N_i|N_i,N_i|v_Ga,v_Ga|v_N,v_N"
        },
        "group_names_with_key_function": {
            "format": "str",
            "value": "N_i:0|N_i:1|v_Ga|v_N"
        }
    }
    
    errors = []
    
    for property_name, expected_info in expected_properties.items():
        expected_value = expected_info['value']
        expected_format = expected_info['format']
        
        if property_name not in properties:
            errors.append(f"{property_name} not found in input properties")
            continue
        
        actual_value = properties[property_name]
        
        # Check type
        if not isinstance(actual_value, eval(expected_format)):
            errors.append(f"{property_name} is not of type {expected_format}")
            continue
        
        # Check value
        if actual_value != expected_value:
            errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"