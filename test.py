#!/usr/bin/env python
# -*- coding:utf-8 -*-
""" 
@author:longlong 
@file: test.py 
@time: 2022/06/25 
@Description: 
@version: 1.0
"""
import requests
import re
import os

with open('exist.txt', 'r') as f:
    data = f.readlines()
    for line in data:
        line_list = line.split('\\')
        print(line_list[-2])