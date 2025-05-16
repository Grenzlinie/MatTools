import docker
import tempfile
import tarfile
import os
import uuid
import pickle
import io
class DockerSandbox:
    def __init__(self, image: str = "mat-tool-ben", container_name: str = "mat_tool_sandbox"):
        self.client = docker.from_env()
        self.image = image
        self.container_name = container_name

    def execute_code(self, code: str) -> str|dict:
        """Execute the given Python code in a Docker container and return the output."""
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as temp_code_file:
                temp_code_file.write(code)
                temp_code_file.flush()

                unique_id = str(uuid.uuid4())[:8]
                container_name = f"{self.container_name}_{unique_id}"
                container = self.client.containers.create(
                    self.image,
                    command="python /app/main.py",
                    working_dir="/app",
                    detach=True,
                    name=container_name
                )

                with tempfile.NamedTemporaryFile() as temp_tar_file:
                    with tarfile.open(temp_tar_file.name, mode='w') as tar:
                        tar.add(temp_code_file.name, arcname='main.py')
                    temp_tar_file.flush()

                    with open(temp_tar_file.name, 'rb') as tar_data:
                        container.put_archive('/app', tar_data.read())

                container.start()
                container.wait()

                # 分离捕获stdout和stderr
                stdout_logs = container.logs(stdout=True, stderr=False).decode('utf-8').strip()
                stderr_logs = container.logs(stdout=False, stderr=True).decode('utf-8').strip()

                container.remove()

                return {
                    "stdout": stdout_logs,
                    "stderr": stderr_logs,
                }

        except docker.errors.DockerException as e:
            return f"Docker error during execution: {str(e)}"
        except Exception as e:
            return f"Error during execution: {str(e)}"

    def execute_file(self, params_dict: dict, py_filename: str, function_name: str) -> str:
            """
            在 Docker 容器中执行指定的 Python 文件中的特定函数，支持复杂对象参数。
            
            参数:
                params_dict: 要传递给 Python 函数的参数字典（支持pickle序列化的对象）
                py_filename: 要执行的 Python 文件名（本地文件系统上的路径）
                function_name: 要调用的函数名称
                
            返回:
                执行输出结果
            """
            try:
                # 检查文件是否存在
                if not os.path.isfile(py_filename):
                    return f"Error: File {py_filename} does not exist"
                
                # 读取源文件内容
                with open(py_filename, 'r') as f:
                    source_code = f.read()
                
                # pickle 序列化参数
                try:
                    params_bytes = pickle.dumps(params_dict)
                except Exception as e:
                    return f"参数序列化失败: {str(e)}"

                # 创建唯一的容器名称
                unique_id = str(uuid.uuid4())[:8]
                container_name = f"{self.container_name}_{unique_id}"
                
                # 创建包装器脚本
                wrapper_script = f"""
import json
import sys
import pickle

# 用户原始代码
{source_code}

if __name__ == "__main__":
    try:
        # 加载参数
        with open('/app/params.pkl', 'rb') as f:
            params = pickle.load(f)
            
        # 验证函数存在性
        if '{function_name}' not in locals():
            print(f"错误：模块中未找到函数 '{{function_name}}'")
            sys.exit(1)
            
        # 执行目标函数
        target_function = locals()['{function_name}']
        result = target_function(params)
        
        # 处理结果输出
        try:
            # 尝试JSON序列化，失败时转为字符串
            print(json.dumps(result, default=lambda o: repr(o)))
        except:
            print(str(result))
            
    except Exception as e:
        print(f"执行过程中发生错误: {{str(e)}}")
        sys.exit(1)
"""
                # 创建临时包装器文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_wrapper_file:
                    temp_wrapper_file.write(wrapper_script)
                    wrapper_path = temp_wrapper_file.name

                # 创建容器并配置文件
                container = self.client.containers.create(
                    self.image,
                    command="python /app/wrapper.py",
                    working_dir="/app",
                    detach=True,
                    name=container_name
                )

                # 构建包含必要文件的tar包
                with tempfile.NamedTemporaryFile() as temp_tar_file:
                    with tarfile.open(temp_tar_file.name, mode='w') as tar:
                        # 添加包装器脚本
                        tar.add(wrapper_path, arcname='wrapper.py')
                        
                        # 添加参数文件
                        params_info = tarfile.TarInfo(name='params.pkl')
                        params_info.size = len(params_bytes)
                        tar.addfile(params_info, io.BytesIO(params_bytes))
                    
                    # 上传文件到容器
                    with open(temp_tar_file.name, 'rb') as tar_data:
                        container.put_archive('/app', tar_data.read())

                # 启动并等待容器执行
                container.start()
                exit_status = container.wait()
                logs = container.logs().decode('utf-8').strip()
                container.remove()
                os.unlink(wrapper_path)

                # 处理执行结果
                if exit_status['StatusCode'] != 0:
                    return f"执行失败（状态码 {exit_status['StatusCode']}）:\n{logs}"
                return logs

            except docker.errors.DockerException as e:
                return f"Docker 错误: {str(e)}"
            except Exception as e:
                return f"执行过程中发生异常: {str(e)}"