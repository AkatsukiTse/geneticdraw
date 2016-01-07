#coding:utf-8
from PIL import Image,ImageDraw, ImageFilter
import random
import time
import math
import logging
import os
import sys
import numpy as np

#三角形
class Polygon(object):
    def __init__(self, pos, color, size):
        if len(pos) < 2: raise Exception
        self.pos = pos
        self.color = color
        self.size = size
        self.img = None

    #变异        
    def mutate(self):  
        if random.random() < 0.5:
            index = random.randrange(0,len(self.pos))
            self.pos[index] = (random.randrange(0,self.size[0]), random.randrange(0,self.size[1]))
        else:
            #颜色变异
            index = random.randrange(0,4)
            self.color[index] = random.randrange(0,256)
            
    def getimg(self):
        if self.img == None:
            img = Image.new('RGBA', self.size)
            draw = ImageDraw.Draw(img)
            draw.polygon(tuple(self.pos), fill=tuple(self.color), outline=tuple(self.color))
            self.img = img
        return self.img
        
#成本计算    
def tcost(vec, originImg):
    
    vecImg = createImgFromVec(vec, originImg.size)
    cost = 0.0
    for y in range(0, originImg.size[1]):
        for x in range(0, originImg.size[0]):
            r1, g1, b1 = originImg.getpixel((x, y))
            r2, g2, b2 = vecImg.getpixel((x, y))
            d_r = r1 - r2
            d_b = b1 - b2
            d_g = g1 - g2
            cost += math.sqrt(d_r * d_r + d_g * d_g + d_b * d_b )
    return cost
    '''
    vecData = np.array(vecImg.convert('RGB'))
    oData = np.array(originImg.convert('RGB'))
    std = oData - vecData
    std[std<0] = std[std<0] * -1
    return std.sum()
    '''

#将三角形数组转换为图像    
def createImgFromVec(vec, size):
    target = Image.new('RGB', size, (255, 255, 255, 255))
    for polygon in vec:
        target.paste(polygon.getimg(), mask=polygon.getimg())
    return target

    
    
'''
创建随机三角形
'''    
def createPolygon(size, posNum):
    pos = [(random.randrange(0, size[0]), random.randrange(0,size[1])) for i in range(posNum)]
    color = [(random.randrange(0, 256)) for i in range(4)]        
    polygon = Polygon(pos, color, size)
    return polygon                    

    
#遗传优化    
def geneticoptimize(costf, img, imgdir='imgs', polygonNum=50, posNum=3, popsize=50, step=10, mutprob=0.5, elite=0.2, maxiter=100):         
    if not os.path.exists(imgdir): os.makedirs(imgdir)  
    #创建集群  
    pop = [createPolygon(img.size,posNum) for i in range(polygonNum)]
    bestscore = costf(pop, img)
    #主循环
    lastscore = None
    itertime = 0
    i = 1
    totalTime = 0
    while i < maxiter:
        evalution = False
        k = random.randrange(0,polygonNum)
        old = pop[k]
        new = Polygon(old.pos, old.color, img.size)        
        new.mutate()
        pop[k] = new
        newscore = costf(pop, img)
        if newscore < bestscore:
            bestscore = newscore
            i += 1
            evalution = True            
        else: 
            pop[k] = old
        #打印当前最优值
        if evalution :
            score = bestscore
            nowtime = time.time()
            if lastscore != None:                
                duration = nowtime - lasttime
                totalTime += duration
                scorestd = lastscore - score
                logImg = createImgFromVec(pop, img.size)
                logImg = logImg.filter(ImageFilter.GaussianBlur(radius=1))
                logImg.save(os.path.join(imgdir,'%d.png'%i))
                print 'times:%6d    score:%7d    scorestd:%7d    duration:%10f    total:%15f'%(i, score, scorestd, duration, totalTime)
                logging.debug('%d\t%d\t%d\t%f\t%f'%(i, score, scorestd, duration, totalTime))
            lasttime = nowtime
            lastscore = score
    return pop

   

   
   
def main(argv):        
    if len(argv) != 2:
            sys.exit(0)
    img = Image.open(argv[1])
    
    localtime = time.localtime()
    logname = '%d%d%d.log'%(localtime.tm_year, localtime.tm_mon, localtime.tm_mday)            
    logging.basicConfig(
        level=logging.DEBUG,
        #format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        format='%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=logname,
        filemode='w')                

    #输入日志
    logfile = open('log.txt', 'w')    
    geneticoptimize(tcost, img, polygonNum=50, maxiter=100000)      


if __name__ == "__main__":
    main(sys.argv)

