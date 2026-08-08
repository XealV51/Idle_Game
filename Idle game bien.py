import pygame
import math
import random as rand
import copy
import pickle
import os

class BigNum:
    def __init__(self, value=0.0, layer=1, hyper = []):
        if isinstance(value, BigNum):
            self.layer = value.layer
            self.hyper = value.hyper
            self.exponent = value.exponent
        elif isinstance(value, str):
            self.layer = layer
            self.hyper = hyper
            self.from_str(value)
        elif value == 0:
            self.layer = 1
            self.hyper = []
            self.exponent = -math.inf 
        else:
            self.layer = layer
            self.hyper = hyper
            self.exponent = math.log(abs(value), 10**layer)
            self.normalize()

    def normalize(self):
        if isinstance(self.layer, BigNum):
            self.exponent = BigNum(self.exponent)
            t = 0
            print(self.layer)
            while self.layer > 5 or self.exponent >= 1e9:
                t+=1
                if self.layer > 1e9:
                    if len(self.hyper)==0:
                        self.hyper.append(1)
                        self.layer = self.layer.log()
                    else:
                        self.hyper[0]+=1
                        self.layer = self.layer.log()
                if self.exponent >= 1e9:
                    self.exponent = self.exponent.log()
                    self.layer+=1

                if t > 1000:
                    print(self.exponent)
                    break
            self.layer = self.layer.to_float
            self.exponent = self.exponent.to_float()
        while self.exponent >= 1e9:  
            self.exponent = math.log10(self.exponent)
            self.layer += 1
        while self.exponent < 9 and self.layer>1:
            self.exponent = 10**self.exponent
            self.layer -= 1
        while self.layer > 1e9:
            if len(self.hyper)==0:
                self.hyper.append(1)
                self.layer = math.log10(self.layer)
            else:
                self.hyper[0]+=1
        if self.layer%1 != 0:
            self.exponent=(10**(self.layer%1))**(self.exponent)
            self.layer=int(self.layer//1)
        while self.layer < 1:
            if self.exponent<=0:
                break #fix negative layers
            else:
                self.exponent = math.log10(self.exponent)
                self.layer += 1
        
    def __repr__(self): 
        if self.exponent == -math.inf: 
            return "0" 
        mantissa = 10 ** (self.exponent % 1) 
        exponent = int(self.exponent // 1) 
        if mantissa>=9.999:
            mantissa=1
            exponent+=1
        if abs(mantissa - 10) < 1e-12:
            mantissa = 1.0
            exponent += 1
        if self.layer <= 1 and len(self.hyper) == 0: 
            if exponent < -4:
                return f"{mantissa:.3f}e{exponent}" 
            if exponent < 0: 
                return f"{(mantissa*10**exponent):.4f}" 
            if exponent < 1: 
                return f"{(mantissa*10**exponent):.3f}" 
            if exponent < 2: 
                return f"{(mantissa*10**exponent):.2f}" 
            elif exponent < 3: 
                return f"{(mantissa*10**exponent):.1f}" 
            elif exponent < 9: 
                return f"{round(mantissa*10**exponent):,}" 
            else: 
                return f"{mantissa:.2f}e{round(exponent):,}" 
        elif len(self.hyper)==0 and self.layer <= 5: 
            return f"{'e'*(self.layer-1)}{mantissa:.2f}e{round(exponent):,}"
        elif len(self.hyper)==0 and self.layer>5:
            if self.layer < 100:
                return f"#{(self.layer+math.log10(self.exponent/10)/9+1):.3f}"
            if self.layer < 100:
                return f"#{(self.layer+math.log10(self.exponent/10)/9+1):.2f}"
            if self.layer < 1e3:
                return f"#{(self.layer+math.log10(self.exponent/10)/9+1):.1f}"
            elif self.layer < 1e4:
                return f"#{(self.layer+math.log10(self.exponent/10)/9+1):.1f}"
            else:
                return f"#{self.layer+1:,}"
        elif len(self.hyper) == 1:
            return f"{'#'*self.hyper[0]}{'e'*(self.layer-1)}{mantissa:.2f}e{exponent:,}"

    def from_str(self, value: str):
        prefix_e_count = 0
        while prefix_e_count < len(value) and value[prefix_e_count] == "e":
            prefix_e_count += 1
        
        self.layer = prefix_e_count + 1 if "e" in value else prefix_e_count
        trimmed_value = value[prefix_e_count:]
        
        if "e" not in trimmed_value:
            self.exponent = math.log10(float(trimmed_value))
        else:
            base, exp_str = trimmed_value.split("e", 1)
            self.exponent = float(exp_str) + math.log10(float(base))
        if not self.exponent or self.layer == 0:
            self.exponent=math.log10(float(value))
            self.layer = 1
        self.normalize()

    def to_float(self):
        if self.exponent == -math.inf:
            return 0.0
        if self.layer > 1:
            raise OverflowError("Number too large to convert to float")
        return 10 ** self.exponent

    def __mul__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if len(self.hyper) == 0 and len(other.hyper) == 0:
            if self.exponent == -math.inf or other.exponent == -math.inf:
                return BigNum(0)
            if self.layer == other.layer == 1:
                return BigNum.from_exponent(self.exponent + other.exponent, self.layer)
            elif self.layer == other.layer == 2:
                x, y = self.exponent, other.exponent
                if x < y:
                    x, y = y, x
                return BigNum.from_exponent(x + math.log10(1 + 10**(y - x)), self.layer)
            elif self.layer < other.layer:
                s = self
                self = other
                other = s
            if self.layer == other.layer + 1 == 2:
                if other.exponent>0:
                    x, y = self.exponent, math.log10(other.exponent)
                    if x < y:
                        x, y = y, x
                    return BigNum.from_exponent(x + math.log10(1 + 10**(y - x)), self.layer)
                else:
                    return self
        return max(self, other)  

    def __truediv__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if len(self.hyper) == 0 and len(other.hyper) == 0:
            if other.exponent == -math.inf:
                raise ZeroDivisionError
            if self.exponent == -math.inf or self.layer < other.layer:
                return BigNum(0)
            if self.layer == other.layer == 1:
                return BigNum.from_exponent(self.exponent - other.exponent, self.layer)
            elif self.layer == other.layer == 2:
                x, y = self.exponent, other.exponent
                if x < y:
                    raise ValueError("Negative result not supported")
                if math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12):
                    return BigNum(0)
                return BigNum.from_exponent(x + math.log10(1 - 10**(y - x)), self.layer)
            elif self.layer < other.layer - 1:
                return 0
            return self
        if self < other:
            return 0
        else:
            return self
        
    def __pow__(self, power):
        if not isinstance(power, BigNum):
            power = BigNum(power)
        if self.exponent==-math.inf:
            return self
        if len(self.hyper) == 0 and len(power.hyper) == 0:
            if self.exponent > 0:
                if self.layer == power.layer:
                    return BigNum.from_exponent(math.log10(self.exponent)+power.exponent, self.layer+1)
                elif self.layer == power.layer + 1:
                    return BigNum.from_exponent(self.exponent + power.exponent, self.layer)
                elif self.layer == power.layer + 2:
                    x, y = self.exponent, power.exponent
                    if x < y:
                        x, y = y, x
                    return BigNum.from_exponent(x + math.log10(1 + 10**(y - x)), self.layer)
                elif self.layer < power.layer:
                    if self.layer == power.layer - 1:
                        x, y = self.exponent, power.exponent
                        if x < y:
                            x, y = y, x
                        return BigNum.from_exponent(x + math.log10(1 + 10**(y - x)), power.layer+1)
                    else:
                        return BigNum.from_exponent(power.exponent, power.layer+1)
                else:
                    return self
            else:
                if power.exponent < 300:
                    return BigNum.from_exponent(self.exponent + self.exponent * (10 ** (power.exponent)-1), self.layer)
                else:
                    return BigNum.from_exponent(-math.inf, self.layer)
        elif self.hyper[0] == 1 :
            if power.hyper[0] == 1:
                if self.layer == 1:
                    x, y = self.exponent, power.exponent
                    if y < 20 and x < 20:
                        z = y+1
                        if 10**y//1 == 10**x//1: 
                            z = y//1 + math.log10(10 ** (y%1*9) + x%1*9)/9 + 1
                        elif 10**y//1 == 10**x//1 + 1: 
                            z = y//1 + math.log10((BigNum(10) ** 10 ** (y%1*9) + x%1*9).log().to_float())/9 + 1
                        elif 10**y//1 == 10**x//1 - 1:
                            z = x//1 + y%1 + x%1
                        return BigNum.from_exponent(z, self.layer, self.hyper)
            elif len(power.hyper) == 0:
                return self
        elif power.hyper[0] == 1:
            if power.layer == 1:
                return BigNum.from_exponent((10**(BigNum(power.exponent))+1).log().to_float(), power.layer, power.hyper)
        return max(self, power)
            
    def __add__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if self.exponent == -math.inf:
            return other
        if other.exponent == -math.inf:
            return self
        if self.layer == other.layer == 1:
            x, y = self.exponent, other.exponent
            if x < y:
                x, y = y, x
            return BigNum.from_exponent(x + math.log10(1 + 10**(y - x)), self.layer)
        return max(self, other) 

    def __sub__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if other.exponent == -math.inf:
            return self
        if self.exponent == -math.inf:
            return BigNum(0)
        if self.layer == other.layer == 1:
            x, y = self.exponent, other.exponent
            if x < y:
                raise ValueError("Negative result not supported")
            if math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12):
                return BigNum(0)
            return BigNum.from_exponent(x + math.log10(1 - 10**(y - x)), self.layer)
        if self < other:
            raise ValueError("Negative result not supported")
        return self

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return BigNum(other).__sub__(self)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return BigNum(other).__truediv__(self)

    def __rpow__(self, other):
        return BigNum(other).__pow__(self)

    def __eq__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if len(self.hyper) == 0:
            return self.layer == other.layer and self.exponent == other.exponent and len(self.hyper) == len(other.hyper)
        else:
            if len(self.hyper) == len(other.hyper) and self.layer == other.layer and self.exponent == other.exponent:
                for i in range(len(self.hyper)):
                    if self.hyper[i] != other.hyper[i]:
                        return False
                return True
            return False

    def __lt__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if len(self.hyper) != len(other.hyper):
            return len(self.hyper) < len(other.hyper)
        if len(self.hyper)>0:
            for i in range(len(self.hyper)):
                j = len(self.hyper)-(i+1)
                if self.hyper[j] != other.hyper[j]:
                        return self.hyper[j] < other.hyper[j] 
        if self.layer != other.layer:
            return self.layer < other.layer
        return self.exponent < other.exponent

    def __le__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if len(self.hyper) != len(other.hyper):
            return len(self.hyper) < len(other.hyper)
        if len(self.hyper)>0:
            for i in range(len(self.hyper)):
                j = len(self.hyper)-(i+1)
                if self.hyper[j] != other.hyper[j]:
                        return self.hyper[j] < other.hyper[j] 
        if self.layer != other.layer:
            return self.layer < other.layer
        return self.exponent <= other.exponent
    
    def __gt__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if len(self.hyper) != len(other.hyper):
            return len(self.hyper) > len(other.hyper)
        if len(self.hyper)>0:
            for i in range(len(self.hyper)):
                j = len(self.hyper)-(i+1)
                if self.hyper[j] != other.hyper[j]:
                        return self.hyper[j] > other.hyper[j] 
        if self.layer != other.layer:
            return self.layer > other.layer
        return self.exponent > other.exponent
    
    def __ge__(self, other):
        if not isinstance(other, BigNum):
            other = BigNum(other)
        if len(self.hyper) != len(other.hyper):
            return len(self.hyper) > len(other.hyper)
        if len(self.hyper)>0:
            for i in range(len(self.hyper)):
                j = len(self.hyper)-(i+1)
                if self.hyper[j] != other.hyper[j]:
                        return self.hyper[j] > other.hyper[j] 
        if self.layer != other.layer:
            return self.layer > other.layer
        return self.exponent >= other.exponent

    @classmethod
    def from_exponent(cls, exponent, layer=1, hyper=[]):
        obj = cls.__new__(cls)
        obj.layer = layer
        obj.exponent = exponent
        obj.hyper = hyper
        obj.normalize()
        return obj

    def log(self, base=10):
        if base <= 0 or base == 1:
            raise ValueError("log base must be > 0 and != 1")
        if isinstance(base, BigNum):
            base = base.to_float()
        if self.exponent == -math.inf:
            return BigNum(0) 
        if len(self.hyper) == 0:
            if self.layer == 1:
                return BigNum(self.exponent * math.log10(10) / math.log10(base))
            return BigNum.from_exponent(self.exponent / math.log10(base), self.layer - 1)   
        return self

    def floor(self):
        if self.exponent == -math.inf:
            return 0

        if self.layer != 1:
            obj = BigNum.from_exponent(self.exponent)
            if hasattr(self, "layer"):
                obj.layer = self.layer
            return obj

        e_int = math.floor(self.exponent)
        frac = self.exponent - e_int
        mant = 10.0 ** frac  

        if e_int <= 15:
            return int(math.floor(mant * (10 ** e_int)))

        obj = BigNum.from_exponent(self.exponent)
        if hasattr(self, "layer"):
            obj.layer = self.layer
        return obj

    def __round__(self, ndigits=0):
        if self.exponent == -math.inf:
            return BigNum(0)

        e_int = math.floor(self.exponent)
        frac = self.exponent - e_int
        mant = 10 ** frac

        rounded_mant = round(mant, ndigits+e_int)

        if rounded_mant >= 10.0:
            rounded_mant /= 10.0
            e_int += 1

        value = rounded_mant * (10 ** e_int)
        return BigNum(value)

    def hyper_exp(self, height, level=2):
        if height == 0: 
            return BigNum(1)
        if level == 1:
            return self ** height
        else:
            if height < 100 and len(self.hyper) == 0:
                if isinstance(height, BigNum):
                    height = height.to_float()
                xt = self
                x = copy.deepcopy(self)
                if height >= 0:
                    if height//1-1>=0:
                        xt = xt.hyper_exp(x ** (height%1), level-1)
                    else:
                        xt = xt ** (height%1)
                    for _ in range(int(height//1-1)):
                        xt = x.hyper_exp(xt, level-1)
                return xt
            elif self < 2**0.5:
                return self.hyper_exp(10)
            elif self == 2**0.5:
                return 2
            elif level == 2:
                if not isinstance(height, BigNum):
                    height = BigNum(height)
                if len(self.hyper) == len(height.hyper) == 0:
                    h = height
                    xt = self
                    if h < BigNum(1e10):
                        h = height.to_float()
                        l = self.layer
                        xt = self
                        x = copy.deepcopy(self)
                        xt = xt ** x ** (h%1)
                        h=h//1-1
                        t=0
                        while xt.layer <= l+1:
                            xt = x ** xt
                            h-=1
                            t+=1
                            if t > 2000:
                                raise "looped too many times"
                        return BigNum.from_exponent(xt.exponent, xt.layer+h, xt.hyper)
                    else:
                        xt = self
                        x = copy.deepcopy(self)
                        t=0
                        l = self.layer
                        while xt.layer <= l+1 :
                            xt = x ** xt
                            h-=1
                            t+=1
                            if t > 2000:
                                print(xt)
                                raise "looped too many times"
                        xt = BigNum.from_exponent(xt.exponent, xt.layer+1e9, xt.hyper)
                        h-=1e9
                        xt.normalize()
                        
                        if xt.layer == 1:
                            if height.exponent < 20:
                                x, y = xt.exponent, math.log10(10**h.exponent-1)
                                if x < y:
                                    x, y = y, x
                            else:
                                x, y = xt.exponent, h.exponent
                                if x < y:
                                    x, y = y, x
                            return BigNum.from_exponent(x + math.log10(1 + 10**(y - x)), xt.layer, xt.hyper)
                        if len(h.hyper) == 0:
                            h.hyper.append(0)
                        return max(self, BigNum.from_exponent(h.exponent, h.layer, [h.hyper[0]+1]))

                elif len(self.hyper) == len(height.hyper) + 1 == 1:
                    if self.hyper[0]==1:
                        if self.layer == 1:
                            if height.exponent < 20:
                                x, y = self.exponent, math.log10(10**height.exponent-1)
                                if x < y:
                                    x, y = y, x
                            else:
                                x, y = self.exponent, height.exponent
                                if x < y:
                                    x, y = y, x
                            return BigNum.from_exponent(x + math.log10(1 + 10**(y - x)), self.layer, self.hyper)
                    if len(height.hyper) == 0:
                        height.hyper.append(0)
                    return max(self, BigNum.from_exponent(height.exponent, height.layer, [height.hyper[0]+1]))
                            
                elif len(self.hyper) == len(height.hyper) == 1:
                    if height.hyper[0] >= self.hyper[0]+1:
                        return BigNum.from_exponent(height.exponent, height.layer, [height.hyper[0]+1])
                    elif height.hyper[0] == self.hyper[0]+1:
                        max(self, BigNum.from_exponent(height.exponent, height.layer, [height.hyper[0]+1]))
                    else:
                        return self
            return max(self, height)

class Seed:

    def __init__(self, value):
        self.a = 1.73149
        self.value = value
        self.b = 0.411 + ((self.value%2**16)**0.5)/613
        self.c = self.value//2**16

    def random(self):
        r = ((self.c + self.a*(self.c+1.03)**self.b))**(1/(1.013+math.log((65536-self.c)**0.5)))*2567894.31%1
        self.a= (self.a+0.98674)%10
        self.b = (self.b+0.0017-0.5)*2%1+0.5
        return r

    def randint(self, min_x, max_x):
        return round(self.random()*(max_x-min_x) + min_x)

pygame.init()

screen_width = 800
screen_height = 400

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("test")

black = (0,0,0)
white = (255, 255, 255)
grey = (127, 127, 127)
blue = (0,0,255)
green = (0,255,0)
magenta = (255,0,255)
orange = (255,127,0)

clock = pygame.time.Clock()
fps = 60
font = pygame.font.Font('freesansbold.ttf', 16)

def reset(level=1):
    global m, max_m, u1, u2, u3, t
    m=BigNum(0)
    max_m = BigNum(0)
    u1={
        "value": BigNum(0),
        "level": 0,
        "cost": BigNum(0),
        "exp": BigNum(1),
        "asc": 0
    }
    if achievments >=2:
        u1["exp"]+=0.05
    u2={
        "value": BigNum(1),
        "level": 0,
        "cost": BigNum(100),
        "mult": 1,
        "asc": 0,
        "mult/20levels":0
    }
    if achievments >= 4:
        u2["mult"]*=1.5
        if achievments >= 9:
            u2["mult/20levels"]+=0.1
    u3={
        "value": BigNum(1),
        "level": 0,
        "cost": BigNum(2000),
        "base": 1.1,
        "asc": 0
    }
    t={
        "value": BigNum(1),
        "exp": BigNum(0.3),
        "gain": BigNum(1),
        "asc": 0
    }
try:
    with open("idle_save", "rb") as f:
        save = pickle.load(f)
    seed = save["seed"]
    m=save["m"]
    max_m = save["max_m"]
    u1=save["u1"]
    u2=save["u2"]
    u3=save["u3"]
    unlocked = save["unlocked"]
    achievments = save["achievments"]
    t = save["t"]
    unlocked_tabs = save["unlocked_tabs"]
    owned_cards=save["owned_cards"]
    draws=save["draws"]
    draw_mult=save["draw_mult"]
    draw_exponent=save["draw_exponent"]

except FileNotFoundError:
    print("noFilesFound Starting a new save")
    seed = Seed(rand.randint(0,2**32-1))
    #idle game    
    unlocked = []
    achievments = 0
    unlocked_tabs = 2
    owned_cards={
        "wait faster":{"value":0, "lvl":0, "exp":0},
        "better power":{"value":0, "lvl":0, "exp":0},
        "ascend more":{"value":1, "lvl":0, "exp":0},
        "faster scaling":{"value":0, "lvl":0, "exp":0},
        "flat mult":{"value":1, "lvl":0, "exp":0},
        "time acceleration":{"value":0, "lvl":0, "exp":0},
        "bigger base":{"value":0, "lvl":0, "exp":0},
        "deck builder":{"value":0, "lvl":0, "exp":0},
        "time ascension":{"value":1, "lvl":0, "exp":0},
        "exponential gain":{"value":0, "lvl":0, "exp":0},
        "fast start":{"value":1, "lvl":0, "exp":0},
        "weaker inflation":{"value":1, "lvl":0, "exp":0},
        "exponential ascension":{"value":0, "lvl":0, "exp":0},
        "crazy scaling":{"value":0, "lvl":0, "exp":0},
        "base upgrading":{"value":0, "lvl":0, "exp":0},
        }
    draws = 0
    draw_mult = 1
    draw_exponent = 2
    reset(999)
#cards
level_up_requirement = [1, 2, 4, 6, 8, 10, 14, 21, 30, 40] #then loops every 10 levels and multiplie by 50
cards = {
    "common":{
        "cards":[
            "wait faster", # t +^0.05/lvl
            "better power", # u1 +^0.02/lvl
            "ascend more", # ascension power x(1+0.1/lvl)
        ],
        "cards values":[
            [BigNum(0), 0.05, "+"],
            [BigNum(0), 0.02, "+"],
            [BigNum(1), 0.1, "+"]
        ],
        "proba":0.65
    },
    "uncommon":{
        "cards":[
            "faster scaling", # u2 mult/20levels +x0.1/lvl and counts each ascensions as 100 lvl for this effect
            "flat mult", # multiplise m+ by (4+lvl)^lvl
            "time acceleration", # t gain increases by +0.005/sec every level
        ],
        "cards values":[
            [BigNum(0), 0.1, "+"],
            [BigNum(4), 1, "+"],
            [BigNum(0), 0.005, "+"]
        ],
        "proba": 0.2
    },
    "rare":{
        "cards":[
            "bigger base", # u3 base increases by +0.03/lvl
            "deck builder", # gets +x1 draws/lvl
            "time ascension", # when t reached 10x(asc+1)^3 t is reset to 0, t exponent is x1.1^asc (+x0.1/lvl)
        ],
        "cards values":[
            [BigNum(0), 0.03, "+"],
            [BigNum(0), 1, "+"],
            [BigNum(1), 0.1, "+"]
        ],
        "proba": 0.1
        },
    "epic":{
        "cards":[
            "exponential gain", # m+ +^0.02/lvl
            "fast start", # t gain is x(5x5^lvl) and then gets divided by t^0.5 (min 1x)
            "weaker inflation", # add x1.1 (+0.1x/lvl) to asc cost exponent divider
        ],
        "cards values":[
            [BigNum(0), 0.02, "+"],
            [BigNum(5), 5, "x"],
            [BigNum(1), 0.1, "+"]
        ],
        "proba": 0.04
    },
    "legendary":{
        "cards":[
            "exponential ascension", # u1 +^0.01/asc (+0.005/lvl after lvl 1)
            "crazy scaling", # u2 mult/20levels is now multiplicative instead of additive but ^0.5 (power isn't applied if lvl<200) and counts each ascensions as 100 lvl for this effect +^0.1/lvl
            "base upgrading" # base increases by (u3["lvl"]^(0.16+0.04*lvl))/25 and counts each ascensions as 100 lvl for this effect
        ],
        "cards values":[
            [BigNum(0.005), 0.005, "+"],
            [BigNum(0.4), 0.1, "+"],
            [BigNum(0.16), 0.04, "+"]
        ],
        "proba": 0.01
    }
}

def draw():
    global owned_cards
    r = seed.random()
    for rarity in cards.values():
        if r<=rarity["proba"]:
            c = seed.randint(0,len(rarity["cards"])-1)
            card = rarity["cards"][c]
            card_value = rarity["cards values"][c]
            break
        else:
            r-=rarity["proba"]
    owned_cards[card]["exp"]+=1
    if owned_cards[card]["exp"]>=level_up_requirement[owned_cards[card]["lvl"]%10]:
        owned_cards[card]["exp"]-=level_up_requirement[owned_cards[card]["lvl"]%10]
        owned_cards[card]["lvl"]+=1
        if card_value[2]=="+":
            owned_cards[card]["value"]=card_value[0]+card_value[1]*owned_cards[card]["lvl"]
        else:
            owned_cards[card]["value"]=card_value[0]*card_value[1]**owned_cards[card]["lvl"]
    return card

last_drawn_card=None
m_inc = 0
u1_rect = pygame.Rect(0, 196, 300, 20)
u2_rect = pygame.Rect(0, 216, 300, 20)
u3_rect = pygame.Rect(0, 236, 300, 20)
menu = 0
running = True
while running:
    mouse = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            #upgrades
            if menu == 0:
                if keys[pygame.K_a] and "buy max" in unlocked:
                    buy_max = True
                else:
                    buy_max = False

                if u1_rect.collidepoint(mouse):
                    while m >= u1["cost"] and u1["level"]<100:
                        u1["level"]+=1
                        m-=u1["cost"]
                        u1["value"] = BigNum(u1["level"])*(5*owned_cards["ascend more"]["value"])**u1["asc"]
                        if u1["level"]<20 or u1["asc"]<1:
                            u1["cost"] = (BigNum(u1["level"])**2+u1["level"])**(1+u1["asc"]/10)**2*(5)**u1["asc"]
                        else:
                            u1["cost"] = (BigNum(u1["level"])**2+u1["level"])**(1+u1["asc"]/10)**(1+(u1["level"]/20)**(u1["asc"]/(10*owned_cards["weaker inflation"]["value"])))*5**u1["asc"]
                        if buy_max == False:
                            break

                    if u1["level"]==100 and "asc" in unlocked:
                        u1["level"]=1
                        u1["asc"]+=1
                        u1["value"] = BigNum(u1["level"])*(5*owned_cards["ascend more"]["value"])**u1["asc"]
                        u1["cost"] = (BigNum(u1["level"])**2+u1["level"])**(1+u1["asc"]/10)**2*5**u1["asc"]

                if u2_rect.collidepoint(mouse) and "u2" in unlocked:

                    while m >= u2["cost"] and u2["level"]<100:
                        u2["level"]+=1
                        m-=u2["cost"]
                        if owned_cards["crazy scaling"]["lvl"]>0:
                            u2["value"] = (1+(BigNum(u2["level"])*0.1))*(u2["mult"]*(u2["mult/20levels"]+owned_cards["faster scaling"]["value"])**(u2["level"]//20+u2["asc"]*5))*(5*owned_cards["ascend more"]["value"])**u2["asc"]
                        elif owned_cards["faster scaling"]["lvl"]>0:
                            u2["value"] = (1+(BigNum(u2["level"])*0.1))*(u2["mult"]+(u2["mult/20levels"]+owned_cards["faster scaling"]["value"])*(u2["level"]//20+u2["asc"]*5))*(5*owned_cards["ascend more"]["value"])**u2["asc"]
                        else:
                            u2["value"] = (1+(BigNum(u2["level"])*0.1))*(u2["mult"]+u2["mult/20levels"]*(u2["level"]//20))*(5*owned_cards["ascend more"]["value"])**u2["asc"]
                        if u2["level"]<20 or u2["asc"]<1:
                            u2["cost"] = (BigNum(u2["level"]**2)*10+100)**(1+u2["asc"]/10)**2*5**u2["asc"]
                        else:
                            u2["cost"] = (BigNum(u2["level"]**2)*10+100)**(1+u2["asc"]/10)**(1+(u2["level"]/20)**(u2["asc"]/(10*owned_cards["weaker inflation"]["value"])))*5**u2["asc"]
                        if buy_max == False:
                            break

                    if u2["level"]==100 and "asc" in unlocked:
                        u2["level"]=1
                        u2["asc"]+=1
                        if owned_cards["crazy scaling"]["lvl"]>0:
                            u2["value"] = (1+(BigNum(u2["level"])*0.1))*(u2["mult"]*(u2["mult/20levels"]+owned_cards["faster scaling"]["value"])**(u2["level"]//20+u2["asc"]*5))*(5*owned_cards["ascend more"]["value"])**u2["asc"]
                        elif owned_cards["faster scaling"]["lvl"]>0:
                            u2["value"] = (1+(BigNum(u2["level"])*0.1))*(u2["mult"]+(u2["mult/20levels"]+owned_cards["faster scaling"]["value"])*(u2["level"]//20+u2["asc"]*5))*(5*owned_cards["ascend more"]["value"])**u2["asc"]
                        else:
                            u2["value"] = (1+(BigNum(u2["level"])*0.1))*(u2["mult"]+u2["mult/20levels"]*(u2["level"]//20))*(5*owned_cards["ascend more"]["value"])**u2["asc"]
                        u2["cost"] = (BigNum(u2["level"]**2)*10+100)**(1+u2["asc"]/10)**2*5**u2["asc"]
                if u3_rect.collidepoint(mouse) and "u3" in unlocked:

                    while m >= u3["cost"] and u3["level"]<100:
                        u3["level"]+=1
                        m-=u3["cost"]
                        if owned_cards["base upgrading"]["lvl"]>0:
                            u3["value"] = BigNum(u3["base"]+owned_cards["bigger base"]["value"]+(u3["level"]+u3["asc"]*100)**owned_cards["base upgrading"]["value"]/25)**(u3["level"]*2**u3["asc"])
                        else:
                            u3["value"] = BigNum(u3["base"]+owned_cards["bigger base"]["value"])**(u3["level"]*2**u3["asc"])
                        if u3["level"]<20 or u3["asc"]<1:
                            u3["cost"] = BigNum(2000) * BigNum(1.25)**(u3["level"]*(2*owned_cards["ascend more"]["value"])**u3["asc"])
                        else:
                            u3["cost"] = BigNum(2000) * BigNum(1.25)**(u3["level"]*(1+(u3["level"]/20)**(u3["asc"]/(10*owned_cards["weaker inflation"]["value"])))**(u3["asc"]))
                        if buy_max == False:
                            break

                    if u3["level"]==100 and "asc" in unlocked:
                        u3["level"]=1
                        u3["asc"]+=1
                        u3["value"] = BigNum(u3["base"])**(u3["level"]*(2*owned_cards["ascend more"]["value"])**u3["asc"])
                        u3["cost"] = BigNum(2000) * BigNum(1.25)**(u3["level"]*5**u3["asc"])
    screen.fill(black)
    if menu == 0:
        #draw text
        screen.blit(font.render(f"m = {m}", True, white), (300,0))

        screen.blit(font.render(f"m+ = {m_inc}", True, white), (5,30))
        if "t" in unlocked:
            screen.blit(font.render(f"t = {t["value"]} = x{t["value"]**((t["exp"]+owned_cards["wait faster"]["value"])*owned_cards["time ascension"]["value"]**t["asc"])} to m+ (^{(t["exp"]+owned_cards["wait faster"]["value"])*owned_cards["time ascension"]["value"]**t["asc"]})", True, white), (5,60))
        if u1["level"]<100:
            screen.blit(font.render(f"u1 = +{u1["value"]**(u1["exp"]+owned_cards["better power"]["value"]+owned_cards["exponential ascension"]["value"]*u1["asc"])} to m+ (lvl:{u1["level"]}, asc: {u1["asc"]}, cost={u1["cost"]})", True, white), (5,200))
        else:
            screen.blit(font.render(f"u1 = +{u1["value"]**u1["exp"]} to m+ (lvl:{u1["level"]}, asc: {u1["asc"]})", True, white), (5,200))
        if "u2" in unlocked:
            if u2["level"]<100:
                screen.blit(font.render(f"u2 = x{u2["value"]} to m+ (lvl:{u2["level"]}, asc: {u2["asc"]}, cost={u2["cost"]})", True, white), (5,220))
            else:
                screen.blit(font.render(f"u2 = x{u2["value"]} to m+ (lvl:{u2["level"]}, asc: {u2["asc"]})", True, white), (5,220))
        if "u3" in unlocked:
            if u3["level"]<100:
                screen.blit(font.render(f"u3 = x{u3["value"]} to m+ (lvl:{u3["level"]}, asc: {u3["asc"]}, cost={u3["cost"]})", True, white), (5,240))
            else:
                screen.blit(font.render(f"u3 = x{u3["value"]} to m+ (lvl:{u3["level"]}, asc: {u3["asc"]})", True, white), (5,240))

    #achievment menu
    if menu == 1:
        if achievments == 0:
            screen.blit(font.render(f"objective: get 100 m", True, white), (300,0))
            screen.blit(font.render(f"reward: u2", True, white), (300,30))
            if m >= 100:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,70))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        unlocked.append("u2")
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False
        if achievments == 1:
            screen.blit(font.render(f"objective: get u1 to level 20", True, white), (300,0))
            screen.blit(font.render(f"reward: +^0.05 to u1", True, white), (300,30))
            if u1["level"] >= 20:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,70))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        u1["exp"]+=0.05
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False
        if achievments == 2:
            screen.blit(font.render(f"objective: get 2,000 m", True, white), (300,0))
            screen.blit(font.render(f"reward: u3", True, white), (300,30))
            if m >= 2000:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,70))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        unlocked.append("u3")
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False
        if achievments == 3:
                    screen.blit(font.render(f"objective: get u2 to level 20", True, white), (300,0))
                    screen.blit(font.render(f"reward: u2 x1.5", True, white), (300,30))
                    if u2["level"]>=20:
                        screen.blit(font.render(f"press enter to get reward", True, white), (300,70))
                        if keys[pygame.K_RETURN]:
                            if not holding_enter:
                                u2["mult"]*=1.5
                                u2["value"] = (1+(BigNum(u2["level"])*0.1))*u2["mult"]
                                achievments+=1
                                holding_enter = True
                        else:
                            holding_enter = False
        if achievments == 4:
            screen.blit(font.render(f"objective: get 10,000 m", True, white), (300,0))
            screen.blit(font.render(f"reward: unlock t (increases by 1 every second)", True, white), (300,30))
            screen.blit(font.render(f"multiplies +m by t^0.3", True, white), (300,50))
            if m >= 1e4:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        unlocked.append("t")
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False
        if achievments == 5:
            screen.blit(font.render(f"objective: get u3 to level 20", True, white), (300,0))
            screen.blit(font.render(f"reward: u3 base +x0.02", True, white), (300,30))
            if u3["level"]>=20:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        u3["base"]+=0.02
                        u3["value"] = BigNum(u3["base"])**u3["level"]
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False

        if achievments == 6:
            screen.blit(font.render(f"objective: get 1,000,000 m", True, white), (300,0))
            screen.blit(font.render(f"reward: ascension", True, white), (300,30))
            if m>1e6:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        unlocked.append("asc")
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False

        if achievments == 7:
            screen.blit(font.render(f"objective: u1 to ascension 2", True, white), (300,0))
            screen.blit(font.render(f"reward: buy max (press a while buying)", True, white), (300,30))
            if u1["asc"]>=2:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        unlocked.append("buy max")
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False

        if achievments == 8:
            screen.blit(font.render(f"objective: u2 to ascension 1", True, white), (300,0))
            screen.blit(font.render(f"reward: u2 +x0.1 per 20 levels", True, white), (300,30))
            if u2["asc"]>=1:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        u2["mult/20levels"]+=0.1
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False

        if achievments == 9:
                    screen.blit(font.render(f"objective: get 1e20 m", True, white), (300,0))
                    screen.blit(font.render(f"reward: prestige", True, white), (300,30))
                    if m>=BigNum("1e20"):
                        screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                        if keys[pygame.K_RETURN]:
                            if not holding_enter:
                                unlocked.append("prestige")
                                unlocked_tabs+=2
                                achievments+=1
                                holding_enter = True
                        else:
                            holding_enter = False
        if achievments == 10:
            screen.blit(font.render(f"objective: get all common cards", True, white), (300,0))
            screen.blit(font.render(f"reward: x2 to draw gain", True, white), (300,30))
            if owned_cards["wait faster"]["lvl"]>=1 and owned_cards["better power"]["lvl"]>=1 and owned_cards["better power"]["lvl"]>=1:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        draw_mult*=2
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False
        if achievments == 11:
            screen.blit(font.render(f"objective: get all uncommon cards", True, white), (300,0))
            screen.blit(font.render(f"reward: x1.5 to draw gain", True, white), (300,30))
            if owned_cards["faster scaling"]["lvl"]>=1 and owned_cards["flat mult"]["lvl"]>=1 and owned_cards["time acceleration"]["lvl"]>=1:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        draw_mult*=1.5
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False
        if achievments == 12:
            screen.blit(font.render(f"objective: get a legendary", True, white), (300,0))
            screen.blit(font.render(f"reward: base card gain ^1.1", True, white), (300,30))
            if owned_cards["exponential ascension"]["lvl"]>=1 or owned_cards["crazy scaling"]["lvl"]>=1 or owned_cards["base upgrading"]["lvl"]>=1:
                screen.blit(font.render(f"press enter to get reward", True, white), (300,90))
                if keys[pygame.K_RETURN]:
                    if not holding_enter:
                        draw_exponent*=1.1
                        achievments+=1
                        holding_enter = True
                else:
                    holding_enter = False
    if menu == 2:
        if m < BigNum("1e20"):
            screen.blit(font.render(f"you need 1e20 m to prestige", True, white), (300,0))
        else:
            draw_gain = (max_m.log()/20)**draw_exponent*(1+owned_cards["deck builder"]["value"])*draw_mult
            screen.blit(font.render(f"you can prestige for {draw_gain} draws", True, white), (300,0))
            screen.blit(font.render(f"press enter to get prestige", True, white), (300,30))
            if keys[pygame.K_RETURN]:
                if not holding_enter:
                    draws+=draw_gain
                    reset(1)
                    holding_enter = True
            else:
                holding_enter = False
    if menu == 3:
        screen.blit(font.render(f"draws = {draws} (press enter to draw)", True, white), (300,0))
        if last_drawn_card!=None:
            screen.blit(font.render(f"you got a {last_drawn_card}", True, white), (300,30))
        if keys[pygame.K_RETURN] and draws>=1:
            if not holding_enter:
                draws-=1
                last_drawn_card=draw()
                holding_enter = True
        else:
            holding_enter = False
        #cards (common)
        if owned_cards["wait faster"]["lvl"]>0:
            screen.blit(font.render(f"wait faster(lvl:{owned_cards["wait faster"]["lvl"]}, {owned_cards["wait faster"]["exp"]}/{level_up_requirement[owned_cards["wait faster"]["lvl"]]}): t +^{owned_cards["wait faster"]["value"]}", True, grey), (0,50))
        if owned_cards["better power"]["lvl"]>0:
            screen.blit(font.render(f"better power(lvl:{owned_cards["better power"]["lvl"]}, {owned_cards["better power"]["exp"]}/{level_up_requirement[owned_cards["better power"]["lvl"]]}): u1 +^{owned_cards["better power"]["value"]}", True, grey), (0,70))
        if owned_cards["ascend more"]["lvl"]>0:
            screen.blit(font.render(f"ascend more(lvl:{owned_cards["ascend more"]["lvl"]}, {owned_cards["ascend more"]["exp"]}/{level_up_requirement[owned_cards["ascend more"]["lvl"]]}): ascension power x{owned_cards["ascend more"]["value"]}", True, grey), (0,90))
        #cards (uncommon)
        if owned_cards["faster scaling"]["lvl"]>0:
            screen.blit(font.render(f"faster scaling(lvl:{owned_cards["faster scaling"]["lvl"]}, {owned_cards["faster scaling"]["exp"]}/{level_up_requirement[owned_cards["faster scaling"]["lvl"]]}): u2 mult/20levels +x{owned_cards["faster scaling"]["value"]} and ascension count as 100 levels now", True, green), (0,110))
        if owned_cards["flat mult"]["lvl"]>0:
            screen.blit(font.render(f"flat mult(lvl:{owned_cards["flat mult"]["lvl"]}, {owned_cards["flat mult"]["exp"]}/{level_up_requirement[owned_cards["flat mult"]["lvl"]]}): m+ x{owned_cards["flat mult"]["value"]**owned_cards["flat mult"]["lvl"]}", True, green), (0,130))
        if owned_cards["time acceleration"]["lvl"]>0:
            screen.blit(font.render(f"time acceleration(lvl:{owned_cards["time acceleration"]["lvl"]}, {owned_cards["time acceleration"]["exp"]}/{level_up_requirement[owned_cards["time acceleration"]["lvl"]]}): t gain increases by +{owned_cards["time acceleration"]["value"]}/sec", True, green), (0,150))
        #cards (rare)
        if owned_cards["bigger base"]["lvl"]>0:
            screen.blit(font.render(f"bigger base(lvl:{owned_cards["bigger base"]["lvl"]}, {owned_cards["bigger base"]["exp"]}/{level_up_requirement[owned_cards["bigger base"]["lvl"]]}): u3 base +{owned_cards["bigger base"]["value"]}", True, blue), (0,170))
        if owned_cards["deck builder"]["lvl"]>0:
            screen.blit(font.render(f"deck builder(lvl:{owned_cards["deck builder"]["lvl"]}, {owned_cards["deck builder"]["exp"]}/{level_up_requirement[owned_cards["deck builder"]["lvl"]]}): +x{owned_cards["deck builder"]["value"]} draws", True, blue), (0,190))
        if owned_cards["time ascension"]["lvl"]>0:
            screen.blit(font.render(f"time ascension(lvl:{owned_cards["time ascension"]["lvl"]}, {owned_cards["time ascension"]["exp"]}/{level_up_requirement[owned_cards["time ascension"]["lvl"]]}): when t reaches 10x(asc+1)^3 t exponent x{owned_cards["time ascension"]["value"]}", True, blue), (0,210))
        #cards (epic)
        if owned_cards["exponential gain"]["lvl"]>0:
            screen.blit(font.render(f"exponential gain(lvl:{owned_cards["exponential gain"]["lvl"]}, {owned_cards["exponential gain"]["exp"]}/{level_up_requirement[owned_cards["exponential gain"]["lvl"]]}): m+ +^{owned_cards["exponential gain"]["value"]}", True, magenta), (0,230))
        if owned_cards["fast start"]["lvl"]>0:
            screen.blit(font.render(f"fast start(lvl:{owned_cards["fast start"]["lvl"]}, {owned_cards["fast start"]["exp"]}/{level_up_requirement[owned_cards["fast start"]["lvl"]]}): t gain is now x{owned_cards["fast start"]["value"]} and then /t^0.5 (min x1)", True, magenta), (0,250))
        if owned_cards["weaker inflation"]["lvl"]>0:
            screen.blit(font.render(f"weaker inflation(lvl:{owned_cards["weaker inflation"]["lvl"]}, {owned_cards["weaker inflation"]["exp"]}/{level_up_requirement[owned_cards["weaker inflation"]["lvl"]]}): x{owned_cards["time ascension"]["value"]} to ascension cost exponent divider", True, magenta), (0,270))
        #cards (legendary)
        if owned_cards["exponential ascension"]["lvl"]>0:
            screen.blit(font.render(f"exponential ascension(lvl:{owned_cards["exponential ascension"]["lvl"]}, {owned_cards["exponential ascension"]["exp"]}/{level_up_requirement[owned_cards["exponential ascension"]["lvl"]]}): u1 +^{owned_cards["exponential ascension"]["value"]}/ascensions", True, orange), (0,290))
        if owned_cards["crazy scaling"]["lvl"]>0:
            screen.blit(font.render(f"crazy scaling(lvl:{owned_cards["crazy scaling"]["lvl"]}, {owned_cards["crazy scaling"]["exp"]}/{level_up_requirement[owned_cards["crazy scaling"]["lvl"]]}): u2 mult/20levels is now multiplicative but ^{owned_cards["crazy scaling"]["value"]} ascensions are worth 100 levels now", True, orange), (0,310))
        if owned_cards["base upgrading"]["lvl"]>0:
            screen.blit(font.render(f"base upgrading(lvl:{owned_cards["base upgrading"]["lvl"]}, {owned_cards["base upgrading"]["exp"]}/{level_up_requirement[owned_cards["base upgrading"]["lvl"]]}): u3 base +(u3 level)^{owned_cards["base upgrading"]["value"]}/25, ascension are worth 100 levels", True, orange), (0,330))
                
    if "t" in unlocked:
        t["value"]+=t["gain"]*max(owned_cards["fast start"]["value"]/t["value"]**0.5,1)/fps
        t["gain"]+=owned_cards["time acceleration"]["value"]/fps
        if owned_cards["time ascension"]["lvl"]>0 and t["value"]>10*(t["asc"]+1)**3:
            t["value"]=BigNum(1)
            t["asc"]+=1
    m_inc = ((u1["value"])**(u1["exp"]+owned_cards["better power"]["value"]+owned_cards["exponential ascension"]["value"]*u1["asc"])*u2["value"]*(t["value"]**((t["exp"]+owned_cards["wait faster"]["value"])*owned_cards["time ascension"]["value"]**t["asc"]))*u3["value"]*owned_cards["flat mult"]["value"])**(1+owned_cards["exponential gain"]["value"])
    m+=m_inc/fps
    if m>max_m:
        max_m = m

    if keys[pygame.K_d]:
        if not holding_d:
            menu= (menu+1)%(unlocked_tabs)
            holding_d = True
    else:
        holding_d = False
    if keys[pygame.K_q]:
        if not holding_q:
            menu= (menu-1)%(unlocked_tabs)
            holding_q = True
    else:
        holding_q = False
    pygame.display.flip()
    clock.tick(fps)

#save game
save = {
        "seed":seed,
        "m":m,
        "max_m":m,
        "u1":u1,
        "u2":u2,
        "u3":u3,
        "unlocked":unlocked,
        "achievments":achievments,
        "t": t,
        "unlocked_tabs": unlocked_tabs,
        "owned_cards": owned_cards,
        "draws": draws,
        "draw_mult": draw_mult,
        "draw_exponent":draw_exponent
    }
with open("idle_save", "wb") as f:
    pickle.dump(save, f)