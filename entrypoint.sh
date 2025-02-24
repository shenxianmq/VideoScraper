#!/bin/bash

# 运行Python程序
python main.py || true

# 保持容器运行
tail -f /dev/null 