def test_cluster_nodes(properties):
    import numpy as np
    expected_properties = {
        "clustered_positions": {
            "format": "np.allclose",
            "value": [[0, 0, 0], [0.25, 0.25, 0.25], [0.5, 0.5, 0.5], [0.75, 0.75, 0.75]]
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
        
        # Check type before numerical comparison
        if expected_format == "np.allclose":
            if not isinstance(actual_value, (list, np.ndarray)):
                errors.append(f"{property_name} is not of type list or np.ndarray")
                continue
            if not np.allclose(actual_value, expected_value, atol=0.001):
                errors.append(f"{property_name}: Expected value close to {expected_value} but got {actual_value}")
        else:
            if actual_value != expected_value:
                errors.append(f"{property_name}: Expected {expected_value} but got {actual_value}")
    
    if errors:
        errors.append(len(errors))
        errors.append(len(expected_properties))
        return errors
    else:
        return "ok"