# -*- coding: utf-8 -*-
"""
@author:xuyuntao
@time:2021/1/20:10:01
@email:xuyuntao@189.cn
"""
import re
import os
import csv
import requests
from bs4 import BeautifulSoup
import time

"""
论文必须为pdf格式，且文件命名为论文题目，可以没有NTFS命名不允许的字符（:等），
但不能将空格( )替换为下划线(_)
路径必须为绝对路径，或者前面包含'.\\'，否则无法识别。
"""

workPath=r".\\testPapers"
logFileName=r"update.log"
logFile=workPath+"\\"+logFileName
updatedPaper=[]
if os.path.isfile(logFile):
    with open(logFile,"r") as f:
        csvRead=csv.reader(f)
        for _ in csvRead:
            updatedPaper+=_
else:
    pass
xueshuURL=r"http://xueshu.baidu.com/s?wd={0}"
paperNameRule=re.compile(r"(被引\d+_)(.*)(\.pdf)")
citationNumRule=re.compile(r"(?<=^被引)(\d+)(?=_)")
folderName=re.compile(r"(?<=\\)\w*?$")
papersProp=[]
for filePath, dirNames, fileNames in os.walk(workPath):
    timeOut=None
    # print(filePath,dirNames,fileNames)
    for fileName in fileNames:
        if fileName == logFileName:  # 遇到log文件跳过
            continue
        paperFolder=re.search(folderName, filePath).group()  # 匹配文件夹名

        citeNumRE=re.search(citationNumRule,fileName) # 匹配文件名中被引数
        if citeNumRE==None:
            citeNum_origin=0
        else:
            citeNum_origin=int(citeNumRE.group())

        paperNameRE=re.search(paperNameRule,fileName)   # 匹配论文名
        if paperNameRE==None:
            paperName=fileName
        else:
            paperName=paperNameRE.group(2)

        if paperName in updatedPaper:  # 如果论文已更新，跳过
            continue
        paperNameFormat = re.sub(r"\s", r"%20", paperName, 0)   # 格式化论文名为url样式
        xueshuWeb = requests.get(xueshuURL.format(paperNameFormat))  # 获取百度学术搜索页
        xueshuWebContent = xueshuWeb.content.decode("utf-8")  # 解码
        xueshuSoup = BeautifulSoup(xueshuWebContent, 'lxml')  # bs格式化
        citeCount = xueshuSoup.find(name='a', attrs={"class": "sc_cite_cont"})  # 搜索被引数标签
        timeOut=xueshuSoup.find(name='div', attrs={"class": "timeout-title"}) # 判断是否限流了
        if timeOut==None:
            if citeCount==None:  # 标签没有出现
                citeNum_new=-1
            else:   # 有标签，匹配其中的数字
                citeNum_new = int(re.search(r"(?<=\s)(\d+)(?=\s)", \
                                            "".join([str(_) for _ in citeCount.contents])\
                                            ).group())
        else:
            break
        papersProp.append([paperFolder, paperName, citeNum_origin, citeNum_new])
        updatedPaper.append(paperName)
        print(papersProp[-1])
        if (citeNum_new>citeNum_origin):
            os.rename(filePath+"\\"+fileName,\
                      filePath+"\\"+"被引{0}_".format(citeNum_new)+paperName+".pdf")
    if timeOut != None:
        print("坑人百度限流啦，等下再试吧！")
        break
with open(logFile,"w",newline="") as f:
    csvWri=csv.writer(f)
    csvWri.writerow(updatedPaper)
print("本次更新了{0}篇期刊文献，共有{1}篇文档已更新。".format(len(papersProp),len(updatedPaper)))


