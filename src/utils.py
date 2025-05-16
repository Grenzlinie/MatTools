import re
import ast
import numpy as np
from pymatgen.core import Element

class ComplexDictParser:
    def __init__(self):
        self.element_dict = {}  # 存储 Element 对象
        self.array_dict = {}    # 存储数组对象
        self.placeholder_counter = 0
    
    def get_new_placeholder(self, prefix):
        placeholder = f"__{prefix}_{self.placeholder_counter}__"
        self.placeholder_counter += 1
        return placeholder
    
    def preprocess_string(self, input_str):
        """预处理字符串，替换复杂对象为占位符"""
        # 首先完整处理所有数组表达式
        result = self._process_arrays(input_str)
        # 然后处理 Element 表达式
        result = self._process_elements_all_formats(result)
        return result
    
    def _find_matching_parenthesis(self, s, start_pos):
        """找到与start_pos位置的左括号匹配的右括号位置"""
        count = 1  # 已找到一个左括号
        pos = start_pos + 1
        
        while pos < len(s) and count > 0:
            if s[pos] == '(':
                count += 1
            elif s[pos] == ')':
                count -= 1
            pos += 1
            
        return pos - 1 if count == 0 else -1
    
    def _process_arrays(self, input_str):
        """处理字符串中的所有数组表达式"""
        result_str = input_str
        # 查找 array( 和 np.array( 模式
        array_patterns = [r'array\(', r'np\.array\(']
        
        for pattern in array_patterns:
            # 不断查找直到找不到为止
            i = 0
            while i < len(result_str):
                match = re.search(pattern, result_str[i:])
                if not match:
                    break
                
                # 计算绝对位置
                start_idx = i + match.start()
                # 查找匹配的右括号
                open_paren_pos = i + match.end() - 1
                close_paren_pos = self._find_matching_parenthesis(result_str, open_paren_pos)
                
                if close_paren_pos == -1:
                    # 没找到匹配的右括号，跳过这个匹配
                    i = start_idx + 1
                    continue
                
                # 提取完整的数组表达式
                array_expr = result_str[start_idx:close_paren_pos+1]
                
                # 创建占位符
                placeholder = self.get_new_placeholder("ARRAY")
                
                try:
                    # 解析数组表达式
                    # 处理 dtype=float128 的情况
                    if 'float128' in array_expr:
                        array_code = array_expr.replace('float128', 'np.float64')
                        if not array_code.startswith('np.'):
                            array_code = 'np.' + array_code
                    else:
                        if array_expr.startswith('array('):
                            array_code = 'np.' + array_expr
                        else:
                            array_code = array_expr
                    
                    # 执行代码创建数组
                    self.array_dict[placeholder] = eval(array_code)
                    
                    # 替换原始表达式为占位符
                    result_str = result_str[:start_idx] + f"'{placeholder}'" + result_str[close_paren_pos+1:]
                    
                    # 由于字符串长度已改变，从替换位置重新开始
                    i = start_idx + len(f"'{placeholder}'")
                    
                except Exception as e:
                    print(f"无法解析数组表达式 '{array_expr}': {e}")
                    # 跳过这个表达式
                    i = start_idx + 1
        
        return result_str
    
    def _process_elements_all_formats(self, input_str):
        """处理所有格式的 Element 表达式"""
        result_str = input_str
        
        # 1. 处理 Element('X') 格式
        pattern1 = r"Element\(['\"](\w+)['\"]\)"
        result_str = self._replace_elements(result_str, pattern1, lambda m: m.group(1))
        
        # 2. 处理 Element X 格式
        pattern2 = r"Element\s+(\w+)"
        result_str = self._replace_elements(result_str, pattern2, lambda m: m.group(1))
        
        return result_str
    
    def _replace_elements(self, input_str, pattern, symbol_extractor):
        """使用给定的模式和符号提取器替换 Element 表达式"""
        result_str = input_str
        element_matches = list(re.finditer(pattern, input_str))
        
        offset = 0
        for match in element_matches:
            start, end = match.span()
            start += offset
            end += offset
            
            try:
                element_symbol = symbol_extractor(match)
                placeholder = self.get_new_placeholder("ELEMENT")
                self.element_dict[placeholder] = Element(element_symbol)
                
                # 替换 Element 表达式为占位符
                result_str = result_str[:start] + f"'{placeholder}'" + result_str[end:]
                offset += len(f"'{placeholder}'") - (end - start)
            except Exception as e:
                print(f"无法创建 Element 对象: {e}")
        
        return result_str
    
    def restore_objects(self, obj):
        """还原所有占位符为原始对象"""
        if isinstance(obj, dict):
            # 处理字典
            new_dict = {}
            for k, v in obj.items():
                new_key = self._restore_single_object(k)
                new_value = self.restore_objects(v)
                new_dict[new_key] = new_value
            return new_dict
        elif isinstance(obj, list):
            # 处理列表
            return [self.restore_objects(item) for item in obj]
        else:
            # 处理单个值
            return self._restore_single_object(obj)
    
    def _restore_single_object(self, obj):
        """还原单个对象"""
        if isinstance(obj, str):
            if obj in self.element_dict:
                return self.element_dict[obj]
            elif obj in self.array_dict:
                return self.array_dict[obj]
        return obj
    
    def parse(self, input_str):
        """解析复杂字符串为 Python 对象"""
        try:
            # 预处理字符串
            preprocessed_str = self.preprocess_string(input_str)
            
            # 使用 ast.literal_eval 解析预处理后的字符串
            parsed_obj = ast.literal_eval(preprocessed_str)
            
            # 还原所有占位符
            result = self.restore_objects(parsed_obj)
            print(f"输入字符串: {input_str}")
            print(f"预处理后的字符串: {preprocessed_str}")
            print(f"解析成功: {result}")
            print("-------------------------------")
            return result
        except Exception as e:
            print(f"输入字符串: {input_str}")
            print(f"预处理后的字符串: {preprocessed_str}")
            print(f"解析错误: {e}")
            print("-------------------------------")
            return None

# Example usage
def parse_complex_string(input_str):
    parser = ComplexDictParser()
    result = parser.parse(input_str)
    return result

# Test the parser
def test_parser():
    print("=== 测试 array 格式带 dtype ===")
    test1 = "{'vibronic_matrix_elements': array([0.0, 3984589.00745148, 0.0, 0.0, 0.0], dtype=float128)}"
    result1 = parse_complex_string(test1)
    print("测试1结果:", result1)
    
    print("\n=== 测试科学记数法 ===")
    test2 = "{'Radiative_Coefficient': array([6.97397183e-31, 6.98245178e-31, 7.38666936e-31], dtype=float128)}"
    result2 = parse_complex_string(test2)
    print("测试2结果:", result2)
    
    print("\n=== 混合元素和数组 ===")
    test3 = "{'element': Element Mg, 'data': array([1.0, 2.0, 3.0])}"
    result3 = parse_complex_string(test3)
    print("测试3结果:", result3)

if __name__ == "__main__":
    test_parser()