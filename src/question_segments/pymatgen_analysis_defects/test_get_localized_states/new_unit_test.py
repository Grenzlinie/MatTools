def test_get_localized_states(properties):
    import numpy as np
    expected_properties = {
        "localized_bands_set_1": {
            "format": "set",
            "value": {138}
        },
        "localized_bands_set_2": {
            "format": "set",
            "value": {75, 77}
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