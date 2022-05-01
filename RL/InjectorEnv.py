# import numpy as np 
# import cv2 
# import gym
# import random
# import time
# import itertools
# import codecs

# from loguru import logger
# from keras.models import load_model
# from gym import Env, spaces
# from collections import defaultdict

from . import utils

class PEBinary():
    def __init__(self, bytepath, asmpath):
        self.bytepath = bytepath
        self.asmpath = asmpath
        
        self.matrix = None 
        self.base_address = None
        self.inject_locations = None
        self.locations_by_section = None
        
        self.init_matrix()
        self.get_inject_locations()
        self.group_locations()
        
    def init_matrix(self):
        try:
            with open(self.bytepath, 'r') as f:
                arr = []
                lines = f.readlines()
                
                # Get base_address
                self.base_address = int(lines[0].split()[0], 16)
                
                for line in lines:
                    vals = line.split()
                    del vals[0]
                    arr.append(vals)
                
                max_len = max([len(vals) for vals in arr])
                
                new_arr = []
                for vals in arr:
                    new_arr.append([val.replace('?', '0') for val in vals])
                
                for vals in new_arr:
                    if '?' in vals:
                        print(vals)
                
                hexstring = ''.join(list(itertools.chain.from_iterable(new_arr)))
                
                byte_arr = bytearray.fromhex(hexstring)
                self.matrix = np.asarray(byte_arr)
            
        except Exception as error:
            logger.error(f"Cant convert bytes to numpy array: {error}")
    
    def inject_NOP(self, data):
        offset = data[0] - self.base_address
        length = data[1]
        
        self.matrix[data[0]: data[0] + data[1]] = 144
        
    def get_inject_locations(self):
        with codecs.open(self.asmpath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            results = []
            idx = 0
            numlines = len(lines)
            while idx < numlines:
                if lines[idx].find('align ') != -1:
                    # print("Processing line", idx, lines[idx])
                    section, address = (lines[idx].replace('\t', ' ').split(' ')[0]).split(':')
                    # print(section, address)
                    
                    found = False
                    while not found:
                        if idx + 1 < numlines:
                            nextline = lines[idx+1]
                            _, next_address = nextline.replace('\t', ' ').split(' ')[0].split(':')
                            if address != next_address:
                                found = True
                                length = int(next_address, 16) - int(address, 16)
                                results.append((section, int(address, 16), length))
                            idx += 1
                        else:
                            found = True
                idx += 1
                
            self.inject_locations = results
            
    def group_locations(self):
        locations = sorted(self.inject_locations, key=lambda x: x[2], reverse=True)
        d = defaultdict(list)
        
        for name, *v in locations:
            d[name].append(v)    
            
        self.locations_by_section = d

class InjectorEnv(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(InjectorEnv, self).__init__()
        
        
        self.model = load_model("./model/checkpoint.h5")
        
        self.bytefolder = ""
        self.asmpfolder = ""
        
        self.action_space = spaces.MultiDiscrete([2000, 2000])
        
        self.observation_shape = ((2000, 2000, 1), (256, 256, 1))
        self.observation_space = spaces.Tuple(
            spaces.Box(low=0, high=255, shape=self.observation_shape[0], dtype=np.unint8), 
            spaces.Box(low=0, high=255, shape=self.observation_shape[1], dtype=np.uint8))
        
        self.max_ninject = 50
        self.injections_left = 50
        
        self.canvas = np.full(self.observation_shape, 255, dtype=np.uint8)

    def step(self, action):
        done = False
        
        assert self.action_space.contains(action), "Invalid Action"
        
        self.injections_left -= 1
        
        if self.injections_left == 0:
            done = True
        
        
        return observation, reward, done, {}
    def reset(self):
        pass
        return observation  # reward, done, info can't be included
    def render(self, mode='human'):
        pass
    def close (self):
        pass
    
if __name__ == "__main__":
    bytepath = "./dataSample/0A32eTdBKayjCWhZqDOQ.bytes"
    asmpath = "./dataSample/0A32eTdBKayjCWhZqDOQ.asm"
    b = PEBinary(bytepath, asmpath)
    
    print(b.locations_by_section)