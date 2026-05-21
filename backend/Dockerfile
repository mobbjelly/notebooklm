FROM python:3.11-slim

WORKDIR /app

# 1. 替换 Debian 软件源为国内镜像（兼容 Debian 11 和 Debian 12）
# 如果是 Debian 12，源配置文件在 /etc/apt/sources.list.d/debian.sources
# 如果是 Debian 11，源配置文件在 /etc/apt/sources.list
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources; \
    else \
        sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
        sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list; \
    fi

# 2. 更新并安装编译依赖（由于换了源，这一步会非常快）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 3. 使用阿里云的 pip 镜像源来加速 Python 依赖包的安装
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]