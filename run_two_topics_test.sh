#!/bin/bash
# 测试两个研究主题的5-variation结果

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
export LLM_PROVIDER=bedrock
export AWS_REGION=us-east-1

export OPENALEX_API_KEY=RKurKTkTC1Q2ulzrCb6ESL
export OPENALEX_MAILTO=xzq@mit.edu

export PUBMED_API_KEY=e4660ed23b8236bd11d4fee034bd15e29b08
export PUBMED_EMAIL=xzq@mit.edu

export SCOPUS_API_KEY=c31cd2f1c2975dd0594c2edc2d3e724d
export SCOPUS_INST_TOKEN=83c7bbb68e010c7d73b85f98c5957b01

# 运行测试（包括OpenAlex, PubMed, Scopus）
python3 test_two_topics_variations.py
