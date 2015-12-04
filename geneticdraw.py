#coding:utf-8
import Image
import ImageDraw
import numpy as np
import random
import thread
import time
import math
import logging
import os
from copy import copy
from copy import deepcopy
from multiprocessing.dummy import Pool as ThreadPool

#三角形
class Polygon(object):
    def __init__(self, pos, color):
        if len(pos) < 2: raise Exception
        self.pos = pos
        self.color = color
        self.img = None

    #变异        
    def mutate(self):
        self.img = None       
        if random.random() < 0.5:
            #点位置变异
            while True:
                index = random.randint(0,len(self.pos)-1)
                step = random.randint(-20,20)
                x = self.pos[index][0]
                y = self.pos[index][1]
                if random.random() < 0.5: 
                    x = x + step
                    x = 0 if x<0 else width if x>width else x                    
                else: 
                    y = y + step
                    y = 0 if y<0 else height if y>height else y 
                self.pos[index] = (x,y)
                #新三角形面积需要大于图像面积的百分之一
                if getS(self.pos[0], self.pos[1], self.pos[2]) > width*height*0.01: break 
        else:
            #颜色变异
            index = random.randint(0,2)
            step = random.randint(-30,30)
            color = self.color[index] + step
            color = colorRange[index][0] \
                if color<colorRange[index][0] \
                else colorRange[index][1] \
                if color>colorRange[index][1] else color
            self.color[index] = color
                
    def getimg(self):
        if self.img == None:
            self.img = Image.new('RGBA', (width,height), (255,255,255,0))
            draw = ImageDraw.Draw(self.img)
            draw.polygon(self.pos, fill=tuple(self.color))
        return self.img 

#计算三角形面积        
def getS(A, B, C):
    try:
        a = math.sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)
        b = math.sqrt((A[0]-C[0])**2 + (A[1]-C[1])**2)
        c = math.sqrt((B[0]-C[0])**2 + (B[1]-C[1])**2)
        p = 0.5*(a+b+c)
        s = math.sqrt(p*(p-a)*(p-b)*(p-c))
    except:
        s = 0
    #print s
    return s

#个体成本计算    
def tcost(vec):
    img = createImgFromVec(vec)
    data = np.array(img.convert('RGB'))
    std = data - origindata
    std[std<0] = std[std<0] * -1
    return std.sum()

#将三角形数组转换为图像    
def createImgFromVec(vec):
    img = Image.new('RGBA', (width,height), (255,255,255,0))    
    for triangle in vec:
        tempimg = triangle.getimg()
        img.paste(tempimg, mask=tempimg)        
    return img

#判断一个点是否在三角形中    
def isinTraiangle(a, b, c, p):
    def Dot(va, vb):
        return va[0]*vb[0] + va[1]*vb[1]
        
    v0 = (c[0]-a[0], c[1]-a[1])
    v1 = (b[0]-a[0], b[1]-a[1])
    v2 = (p[0]-a[0], p[1]-a[1])
    
    dot00 = Dot(v0, v0)
    dot01 = Dot(v0, v1)
    dot02 = Dot(v0, v2)
    dot11 = Dot(v1, v1)
    dot12 = Dot(v1, v2)
    try:
        inverDeno = 1.0 / (dot00*dot11 - dot01*dot01)
    except:
        return False    
    u = (dot11*dot02 - dot01*dot12) * inverDeno
    if u < 0 or u > 1: return False
    v = (dot00*dot12 - dot01*dot02) * inverDeno
    if v < 0 or v > 1: return False
    return u + v <= 1
    
    
'''
创建随机三角形
'''    
def createPolygon(xlimit, ylimit, posNum):
    while True:
        pos = [(random.randint(xlimit[0],xlimit[1]-1), random.randint(ylimit[0],ylimit[1]-1)) \
                for i in range(posNum)]
        #新三角形面积需要大于图像面积的百分之一
        if getS(pos[0], pos[1], pos[2]) > width*height*0.01: break 
    color = [(random.randint(colorRange[i][0], colorRange[i][1])) for i in range(3)]        
    color.append(128)
    polygon = Polygon(pos, color)
    return polygon                    
    
#遗传优化    
def geneticoptimize(costf, polygonNum=50, popsize=50, step=1, mutprob=0.5, elite=0.2, maxiter=100):           
    #创建集群  
    pop = [createPolygon((0,width),(0,height),posNum) for i in range(polygonNum)]
    bestscore = costf(pop)
    #主循环
    lastscore = None
    top = polygonNum*mutprob
    itertime = 0
    i = 1
    totalTime = 0
    lastindex = None
    while i < maxiter:
        evolution = False
        #pop = sorted(pop, key=lambda x:x.score)
        k = lastindex if lastindex != None else random.randint(0,len(pop)-1)
        old = pop[k]
        new = Polygon(old.pos, old.color)
        new.mutate()
        pop[k] = new
        newscore = costf(pop)
        if newscore < bestscore:
            bestscore = newscore
            i += 1
            evolution = True
            lastindex = k            
        else: 
            pop[k] = old
            lastindex = None
        #打印当前最优值
        if evolution and i%10 == 0:
            score = bestscore
            nowtime = time.time()
            if lastscore != None:                
                duration = nowtime - lasttime
                totalTime += duration
                scorestd = lastscore - score
                img = createImgFromVec(pop)
                img.save(os.path.join(imgdir,'%d.png'%i))
                print 'times:%6d    score:%7d    scorestd:%7d    duration:%10f    total:%15f'%(i, score, scorestd, duration, totalTime)
                logging.debug('%d\t%d\t%d\t%f\t%f'%(i, score, scorestd, duration, totalTime))
            lasttime = nowtime
            lastscore = score
    return pop

   

localtime = time.localtime()
logname = '%d%d%d.log'%(localtime.tm_year, localtime.tm_mon, localtime.tm_mday)            
logging.basicConfig(
    level=logging.DEBUG,
    #format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    format='%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename=logname,
    filemode='w') 
    
imgdir = 'imgs'
if not os.path.exists(imgdir): os.makedirs(imgdir)
#多边形的顶点数
posNum = 3
#测试图片
img = Image.open('test.jpg')
origindata = np.array(img)
width, height = img.size
print 'width:%5d,height:%5d'%(width,height)
#获取图片颜色范围 
colorRange = ((origindata[:,:,0].min(),origindata[:,:,0].max()),
                (origindata[:,:,1].min(),origindata[:,:,1].max()),
                (origindata[:,:,2].min(),origindata[:,:,2].max()))
whitedata = np.array(Image.new('RGBA', (100,155), 'white'))
geneticoptimize(tcost, polygonNum=100, maxiter=100000)

