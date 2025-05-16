# 使用 Python 3.11.8 官方镜像作为基础镜像 Use Python 3.11.8 official image as the base image
FROM python:3.11.8

# 设置工作目录 Set the working directory
WORKDIR /app

# 将 src/tool_source_code 文件夹和 requirements.txt 复制到镜像中 Copy the src/tool_source_code folder and requirements.txt to the image
COPY src/tool_source_code /app/tool_source_code
COPY requirements.txt /app/requirements.txt

# 安装依赖 Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# 设置默认命令为空，这样容器不会在启动时执行任何操作 Set the default command to empty, so the container does not execute any operations when started
CMD ["bash"]