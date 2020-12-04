import matplotlib.pyplot as plt
import numpy as np

class Stack():
    def __init__(self):
        self.durations = []
        self.times = []
        self.types = []
        self.names = []

    # types:
    # 0 - atonement
    # 1 - boon
    # 2 - damage
    # 3 - rapture atonement
    # 4 - misc
    def push(self, duration, time, name, dtype=0):
        self.durations.append(duration)
        self.times.append(time)
        self.types.append(dtype)
        self.names.append(name)

    def __len__(self):
        return len(self.durations)

def gcd(haste, val=1.5):
    return max(1.5/(1+haste), 0.75)

def casttime(normaltime, haste):
    return normaltime/(1+haste)

class Ability():
    def __init__(self, cast_time=0):
        self.ct = cast_time

    def mod_stack(self, stack, current_time, haste):
        pass

    def push(self, stack, duration, time, **kwargs):
        stack.push(duration, time, self.__class__.__name__, **kwargs)

    def wait_time(self, stack, current_time, haste):
        # Used for waiting for cooldowns
        return 0

    def after_cast_time(self, haste, val=1.5):
        # by default just the GCD, but channeling is just a higher value for this
        return max(0, gcd(haste, val=val) - casttime(self.ct, haste))

    def cast(self, stack, current_time, haste, rapture=False, com=False):
        ct = casttime(self.ct, haste)
        current_time += ct
        current_time += self.wait_time(stack, current_time, haste)
        self.mod_stack(stack, current_time, haste, rapture=rapture, com=com)
        current_time += self.after_cast_time(haste)
        return current_time

class Shield(Ability):
    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        duration = 21 if rapture and com else 15
        dtype = 3 if rapture else 0
        self.push(stack, duration, current_time, dtype=dtype)

class Rapture(Shield):
    pass

class SMend(Ability):
    def __init__(self):
        super().__init__(1.5)

    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 15, current_time)

class Radiance(Ability):
    def __init__(self):
        super().__init__(2)

    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 9, current_time)
        self.push(stack, 9, current_time)
        self.push(stack, 9, current_time)
        self.push(stack, 9, current_time)
        self.push(stack, 9, current_time)

class Evang(Ability):
    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        for i in range(len(stack)):
            if stack.types[i] not in [0, 3]:
                continue
            if current_time - stack.times[i] < stack.durations[i]:
                stack.durations[i] += 6
        self.push(stack, 0.2, current_time, dtype=4)

class Damage(Ability):
    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 0.2, current_time, dtype=2)

class Schism(Damage):
    def __init__(self):
        super().__init__(1.5)

class Penance(Damage):
    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, casttime(2, haste), current_time, dtype=2)

    def after_cast_time(self, haste):
        # by default just the GCD, but channeling is just a higher value for this
        return casttime(2, haste)

class Solace(Damage):
    pass

class Boon(Ability):
    def __init__(self):
        super().__init__(1.5)

    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 10, current_time, dtype=1)
        
class ABlast(Damage):
    def wait_time(self, stack, current_time, haste):
        cd = 3
        last_time = -9999999
        for i in range(len(stack)):
            if stack.names[i] == self.__class__.__name__:
                last_time = max(last_time, stack.times[i])
        return max(0, 3.001 + last_time - current_time)

    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        buff_found = False
        for i in range(len(stack)):
            if stack.names[i] == self.__class__.__name__:
                if current_time - stack.times[i] < 3:
                    raise ValueError('ABlast is on cooldown!')

            if stack.types[i] == 1:
                if current_time - stack.times[i] < stack.durations[i]:
                    buff_found = True

        if not buff_found:
            raise ValueError('ABlast cast outside of Boon!')
        super().mod_stack(stack, current_time, haste, rapture=rapture, com=com)
    
    def after_cast_time(self, haste, val=1.5):
        return super().after_cast_time(haste, val=1.0)

class MBlast(Damage):
    def __init__(self):
        super().__init__(1.5)

class Smite(Damage):
    def __init__(self):
        super().__init__(1.5)

class Fiend(Damage):
    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 15, current_time, dtype=2)

class SWP(Damage):
    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 12, current_time, dtype=2)

class PI(Ability):
    def after_cast_time(self, haste):
        return 0

    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 20, current_time, dtype=4)


class Halo(Ability):
    def __init__(self):
        super().__init__(1.5)

    def mod_stack(self, stack, current_time, haste, rapture=False, com=False):
        self.push(stack, 0.2, current_time)

# How to fit in Boon?
# Which of Boon, Evang, Power Infusion, Rapture, Fiend, Halo to mix together, and what order to do them in?

name = 'Boon no com no fiend no pi'
haste = 0.1
rapture_duration = 8
pi_duration = 20
rapture_leggo = False
#casts = [SWP(), PI(), Rapture()] + [Shield()]*9 + [SWP(), Radiance(), Radiance(), Evang(), Boon(), ABlast(), Schism(), ABlast(),  Penance(), ABlast(), Solace(), ABlast(), MBlast(), Halo()] # boon com no fiend
#casts = [SWP(), PI(), Rapture()] + [Shield()]*7 + [Radiance(), Radiance(), Evang(), Boon(), ABlast(), Schism(), ABlast(),  Penance(), ABlast(), Solace(), ABlast(), MBlast(), Halo()] # boon no com no fiend
#casts = [SWP(), Rapture()] + [Shield()]*7 + [SWP(), Radiance(), Radiance(), Evang(), Boon(), ABlast(), Schism(), ABlast(),  Penance(), ABlast(), Solace(), ABlast(), MBlast(), Halo()] # boon com no fiend no pi
casts = [SWP(), Rapture()] + [Shield()]*5 + [Radiance(), Radiance(), Evang(), Boon(), ABlast(), Schism(), ABlast(),  Penance(), ABlast(), Solace(), ABlast(), MBlast(), Halo()] # boon no com no fiend no pi
#casts = [SWP(), PI(), Rapture()] + [Shield()]*7 + [Radiance(), Fiend(), Radiance(), SWP(), Evang(), Schism(), Penance(), Solace(), MBlast(), Smite(), Smite(), Smite(), Halo()] # fiend no com
#casts = [SWP(), PI(), Rapture()] + [Shield()]*9 + [Radiance(), Fiend(), Radiance(), SWP(), Evang(), Schism(), Penance(), Solace(), MBlast(), Smite(), Smite(), Smite(), Halo()] # fiend com
#casts = [SWP()] + [Shield()]*5 + [SWP(), Radiance(), Schism(), Penance(), Solace(), MBlast(), Halo()], # mini-ramp

stack = Stack()
current_time = 0
damage_start = 0
rapture = False
power_infusion = False
for cast in casts:
    print(cast.__class__.__name__)
    if cast.__class__.__name__ == 'Rapture':
        rapture = True
        rapture_start = current_time
    if cast.__class__.__name__ == 'PI':
        power_infusion = True
        pi_start = current_time
        haste += 0.25

    if not damage_start and cast.__class__.__name__ in ['ABlast']:
        damage_start = current_time

    current_time = cast.cast(stack, current_time, haste, rapture=rapture, com=rapture_leggo)

    if not damage_start and cast.__class__.__name__ in ['Schism']:
        damage_start = current_time


    if rapture and current_time - rapture_start >= rapture_duration:
        rapture = False
    if power_infusion and current_time - pi_start >= pi_duration:
        power_infusion = False
        haste -= 0.25

y = ['%d: %s' % (i, name) for i, name in enumerate(stack.names)]
width = stack.durations
height = 0.9
left = stack.times

colors = {0: 'green', 1: 'blue', 2: 'red', 3: 'lightgreen', 4: '#444444'}
color = [colors[t] for t in stack.types]

plt.figure(figsize=(12, 8))
plt.grid(b=True, which='major', color='#aaaaaa', axis='x', linestyle='-', zorder=0)
plt.barh(y, width, height=height, left=left, color=color, zorder=3)
plt.axvline(x=damage_start)
plt.gca().invert_yaxis()
plt.xlabel('Time (s)')
plt.title('%s, Haste: %d%%, Rapture Legendary: %r' %  (name, int(haste*100+0.5), rapture_leggo))
plt.tight_layout()
plt.savefig(name.lower().replace(' ', '_')+'.png')
plt.show()
