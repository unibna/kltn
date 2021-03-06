import numpy as np 
import cv2 
import gym
import random
import time
import itertools
import codecs
import math
import os

from loguru import logger
from keras.models import load_model
from gym import Env, spaces
from collections import defaultdict

import utils

class PEBinary():
    def __init__(self, bytepath, asmpath):
        self.bytepath = bytepath
        self.asmpath = asmpath
        
        self.matrix = None 
        self.base_address = None
        self.inject_locations = None
        self.locations_by_section = None
        # Number of sections in the binary
        self.nsections = None
        
        self.init_matrix()
        self.get_inject_locations()
        
        self.nsections = self.group_locations()
        
        
    def init_matrix(self):
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
            
        
            raw_width = math.floor(math.sqrt(len(byte_arr)))
            
            rem = len(byte_arr) % raw_width
            byte_arr_len = len(byte_arr) - rem
            byte_arr = byte_arr[:byte_arr_len]
            byte_arr = np.asarray(byte_arr)
            np_arr = np.reshape(byte_arr, (len(byte_arr)// raw_width, raw_width))
            np_arr = np.uint8(np_arr)
            
            self.matrix = np_arr

    
    def inject(self, data, value):
        offset = data[0] - self.base_address
        length = data[1]
        print("Injecting at", offset, " with length ", length)
        self.matrix[offset: offset + length] = value
        
    def inject_section(self, section, value):
        for loc in self.locations_by_section[section]:
            self.inject(loc, value)


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
        
        return len(self.locations_by_section.keys())
        
    

class InjectorEnv(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(InjectorEnv, self).__init__()

        self.model = load_model("C:\\Users\\hao.le\\Documents\\Projects\\Thesis\\kltn\\model\\checkpoint.h5")

        self.bytefolder = "D:\\Big2015\\dataset-10-8-2\\8-2-0.0\\train-bytes\\1"
        self.asmfolder = "D:\\Big2015\\dataset-10-8-2\\8-2-0.0\\8.2.0.0-asm\\train-asm\\1"
        
        self.bytes = []
        self.asms = []
        
        self.action_space = spaces.MultiDiscrete([5, 255])
        
        self.observation_shape = ((256, 256, 1), 1)
        self.observation_space = spaces.Tuple((spaces.Box(low=0, high=255, shape=self.observation_shape[0], dtype=np.uint8),
                                              spaces.Discrete(5)))
        
        self.max_injections = 50
        self.injections_left = 50
        self.current_file_idx = -1
        self.PEBinary = None
        
        self.canvas = np.full(self.observation_shape[0], 255, dtype=np.uint8)
        self.nsections = 0
        
        self.load_input()

    def load_input(self):
        for file in os.listdir(self.bytefolder):
            if file.endswith(".bytes"):
                path = os.path.join(self.bytefolder, file)
                self.bytes.append(path)
                
        for file in os.listdir(self.asmfolder):
            if file.endswith(".asm"):
                path = os.path.join(self.asmfolder, file)
                self.asms.append(path)
                
        valid = False
        while not valid:
            valid = self.next_file()
        
        
    def next_file(self):
        if self.current_file_idx >= len(self.bytes):
            self.current_file_idx = 0
        else:
            self.current_file_idx += 1
        self.PEBinary = PEBinary(self.bytes[self.current_file_idx],
                                 self.asms[self.current_file_idx])
        self.nsections = self.PEBinary.nsections
        
        if self.nsections > 5:
            return False
        return True

    def step(self, action):
        done = False
        reward = 0
        
        assert self.action_space.contains(action), "Invalid Action"
        
        self.injections_left -= 1
        
        if self.injections_left == 0:
            done = True
        
        section_idx = action[0]
        code = action[1]
        
        keys = list(self.PEBinary.locations_by_section.keys())
        if section_idx < len(keys):
            section = keys[section_idx]
            self.PEBinary.inject_section(section, code)
        else:
            reward = -10
        
        self.update_canvas()
        
        return (self.canvas, self.nsections) , reward, done, {}
    
    def update_canvas(self):
        img = utils.np2img(self.PEBinary.matrix, 256, 256)
        self.canvas = np.asarray(img)

    def reset(self):
        # Reset the number of injections left
        self.injections_left = self.max_injections
        
        # Get next input file
        self.next_file()
        
        # Map PE Binary to canvas (256 x 256)
        self.update_canvas()

        # # Draw elements on the canvas
        # self.draw_canvas()
        
        return (self.canvas, self.nsections)  # reward, done, info can't be included
    
    def render(self, mode='human'):
        assert mode in ["human", "rgb_array"], "Invalid mode, must be either \"human\" or \"rgb_array\""
        if mode == "human":
            cv2.imshow("Game", self.canvas)
            cv2.waitKey(10)
        
        elif mode == "rgb_array":
            return self.canvas

    def close (self):
        cv2.destroyAllWindows()
    
if __name__ == "__main__":
    bytepath = "./dataSample/0A32eTdBKayjCWhZqDOQ.bytes"
    asmpath = "./dataSample/0A32eTdBKayjCWhZqDOQ.asm"
    env = InjectorEnv()
    obs = env.reset()
    
    from stable_baselines3.common import env_checker
    env_checker.check_env(env)