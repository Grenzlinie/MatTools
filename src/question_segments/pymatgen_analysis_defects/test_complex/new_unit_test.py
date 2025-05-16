def test_complex(properties):
    import numpy as np
    from pymatgen.core import Element
    
    expected_properties = {
        "defect_complex_name": {
            "format": "str",
            "value": "O_N+v_Ga"
        },
        "supercell_structure_formula": {
            "format": "str",
            "value": "Ga63 N63 O1"
        },
        "defect_complex_oxidation_state": {
            "format": "bool",
            "value": True
        },
        "element_changes": {
            "format": "dict",
            "value": {Element('Ga'): -1, Element('N'): -1, Element('O'): 1}
        },
        "defect_structure_formula": {
            "format": "str",
            "value": "Ga1 N1 O1"
        },
        "defect_complex_with_interstitial_name": {
            "format": "str",
            "value": "O_N+v_Ga+H_i"
        },
        "supercell_structure_with_dummy_formula": {
            "format": "str",
            "value": "Ga63 H1 Xe1 N63 O1"
        },
        "defect_complex_equality": {
            "format": "bool",
            "value": True
        },
        "defect_complex_inequality": {
            "format": "bool",
            "value": True
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
        
        # Check type (skip type check for np.allclose cases as it's handled separately)
        if expected_format != "np.allclose" and not isinstance(actual_value, eval(expected_format)):
            errors.append(f"{property_name} is not of type {expected_format}")
            continue
        
        # Check value or use np.allclose for approximate comparisons
        if expected_format == "np.allclose":
            if not np.allclose(actual_value, expected_value):
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