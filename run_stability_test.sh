#!/bin/bash
# 运行查询稳定性测试脚本

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
export LLM_PROVIDER=bedrock
export AWS_REGION=us-east-1

export OPENALEX_API_KEY=RKurKTkTC1Q2ulzrCb6ESL
export OPENALEX_MAILTO=xzq@mit.edu

export PUBMED_API_KEY=e4660ed23b8236bd11d4fee034bd15e29b08
export PUBMED_EMAIL=xzq@mit.edu

export SCOPUS_API_KEY=f0f4a2ca58b215d8f580b48f5083dc0c

# 运行测试 - 传入运行次数参数
echo "3" | python3 test_query_stability.py
