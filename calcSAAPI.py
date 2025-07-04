import cloudscraper
import copy
import math
import os
import time # Time used for debugging

from dataclasses import dataclass, field
        
# Class for keeping track of a unit and its kit
@dataclass
class Unit:
    id: int
    name: str
    rarity: str # N, R, SR, SSR, UR, LR
    hp_max: int # Max stat without HiPo
    atk_max: int
    def_max: int
    # Elements in order: AGL, TEQ, INT, STR, PHY (0-4)
    # Super AGL, TEQ, INT, STR, PHY (10-14)
    # Extreme AGL, TEQ, INT, STR, PHY (20-24)
    element1: str # Super, Extreme
    element2: str # AGL, TEQ, INT, STR, PHY
    eball_mod_mid: int # Should be 0 for non-LRs
    eball_mod_mid_num: int # Should be 0 for non-LRs
    eball_mod_max: int
    eball_mod_max_num: int
    title: str
    leader_skill: str
    passive_skill_name: str
    active_skill_name: str
    active_skill_effect: str
    active_skill_condition: str
    passive_skill_itemized_desc: str
    categories: list
    potential: list
    specials: list
    transformations: list
    costumes: list
    optimal_awakening_growths: list
    card_links: list
    finish_skills: list
    standby_skills: list
    dokkan_fields: list
    
    def __init__(self, id, name, rarity, hp_max, atk_max, def_max, element1, element2, 
    eball_mod_mid, eball_mod_mid_num, eball_mod_max, eball_mod_max_num, title,
    leader_skill, passive_skill_name, active_skill_name, active_skill_effect,
    active_skill_condition, passive_skill_itemized_desc, categories, potential, specials,
    transformations, costumes, optimal_awakening_growths, card_links, finish_skills,
    standby_skills, dokkan_fields):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.hp_max = hp_max
        self.atk_max = atk_max
        self.def_max = def_max
        self.element1 = element1
        self.element2 = element2
        self.eball_mod_mid = eball_mod_mid
        self.eball_mod_mid_num = eball_mod_mid_num
        self.eball_mod_max = eball_mod_max
        self.eball_mod_max_num = eball_mod_max_num
        self.title = title
        self.leader_skill = leader_skill
        self.passive_skill_name = passive_skill_name
        self.active_skill_name = active_skill_name
        self.active_skill_effect = active_skill_effect
        self.active_skill_condition = active_skill_condition
        self.passive_skill_itemized_desc = passive_skill_itemized_desc
        self.categories = categories
        self.potential = potential # ATK, DEF, HP
        self.specials = specials
        self.transformations = transformations
        self.costumes = costumes
        self.optimal_awakening_growths = optimal_awakening_growths
        self.card_links = card_links
        self.finish_skills = finish_skills
        self.standby_skills = standby_skills
        self.dokkan_fields = dokkan_fields
        
# Class for keeping track of a linking partner
@dataclass
class Partner:
    id: int
    name: str
    rarity: str
    element2: str
    card_links: list
    
    def __init__(self, id, name, rarity, element2, card_links):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.element2 = element2
        self.card_links = card_links
        
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None  # Reference to the next node

# LinkedList class manages the nodes and operations of the linked list
class LinkedList:
    def __init__(self):
        self.head = None  # Initialize an empty linked list
        
    def insertLine(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node
            return
        last_node = self.head
        while last_node.next:
            last_node = last_node.next
        last_node.next = new_node
        
    def removeLine(self):
        if (self.head == None):
            return
        
        self.head = self.head.next
        
    # Checks if multiple stat buffs have the same condition
    def searchLine(self, condition):
        current = self.head
        while current is not None:
            if (current.data).__contains__(condition):
                return current.data
            current = current.next
        return None
    
    # Adjusts buffs if multiple stat buffs have the same condition
    def replaceLine(self, condition, buff):
        current = self.head
        while current is not None:
            if (current.data).__contains__(condition):
                line1 = current.data.split("+")[0] + "+"
                line2 = (current.data).split("+")[1]
                line2 = int(line2.split("% ")[0]) + int(buff)
                line3 = "% (" + current.data.split("% (")[1]
                current.data = f'{line1}{line2}{line3}'
            current = current.next
        return

# Units that do not fit in terminal:
# - SEZA LR INT SSJ2 Gohan
# - EZA UR PHY Future Android #17
# - EZA UR TEQ Android #18

# Dev Note: Adjust stacking patterns between:
# Units with multiple SAs + multiple stacking patterns (STR Perfect Cell)
# Units with perm + temp raises (TEQ LR Dragon Fist EZA)
# Units with stacking base + temp transformed forms (TEQ Ultimate Gohan?)
# Units with temp base + stacking transformed forms (AGL Turles)
# Units with stacking base + transformed forms (INT UI Goku)

# Dev Note: Adjust AGL LR Gotenks
# Dev Note: Adjust TEQ LR Broly's EZA stacks (Multi-select?)

# Dev Note: Adjust stacking quantities in calculation, refer to additional documentation

def calcActiveATK(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional):
    buff = 0
    flat = True
    if characterKit.active_skill_name:
        if characterKit.active_skill_effect.__contains__('critical hit'):
            crit = True
        
        if (characterKit.active_skill_effect.__contains__('ATK ') and characterKit.active_skill_effect.__contains__('% ') and
        not characterKit.active_skill_effect.__contains__('damage to enemy') and not characterKit.active_skill_effect.__contains__('sacrificing ')):
            buff = characterKit.active_skill_effect.split('ATK ')[1]
            
            if characterKit.active_skill_effect.__contains__(" allies' ATK by"):
                buff = buff.split('by ')[1]
            
            if buff.__contains__('% ') or buff.__contains__('%,'):
                flat = False
                if buff.__contains__('& DEF +'):
                    buff = buff.split('& DEF +')[1]
                buff = int(buff.split('%')[0])
            else:
                buff = int(buff.split(' ')[0])
            print(f'{ATK} (Before Activating Active Skill: "{characterKit.active_skill_name}")')
            calcATKKi(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional)
                
            if flat:
                ATK = int(ATK + buff)
                print(f'{ATK} (With {buff} Flat Buff, After Activating Active Skill: "{characterKit.active_skill_name}")')
            else:
                ATK = int(ATK * (1 + (buff/100)))
                print(f'{ATK} (With {buff}% Buff, After Activating Active Skill: "{characterKit.active_skill_name}")')
                calcATKKi(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional)
        else:    
            calcATKKi(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional)
    else:
        calcATKKi(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional)

def calcATKKi(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional):
    if characterKit.specials:
        baseKiMultiplier = (((200-characterKit.eball_mod_mid)/12)*(characterKit.specials[0][2]-12))+characterKit.eball_mod_mid
        # Adjusts base Ki Multiplier for URs
        if characterKit.rarity == 'UR':
            baseKiMultiplier = (characterKit.eball_mod_max/24)*(12+characterKit.specials[0][2])
        baseATK = int(ATK * (baseKiMultiplier/100)) # Apply base Ki multiplier
        
        for special in characterKit.specials:
            kiMultiplier = (((200-characterKit.eball_mod_mid)/12)*(special[2]-12))+characterKit.eball_mod_mid
            if special[2] == 12:
                if characterKit.rarity != 'LR':
                    kiMultiplier = characterKit.eball_mod_max
                else:
                    kiMultiplier = characterKit.eball_mod_mid
            elif special[2] < 12 and characterKit.rarity != 'LR':
                # (max ki multi - 1)/ki needed to reach 12ki from not being in negative ki multi*the ki obtained
                # for example, to find Gotenks 11ki its (1.4-1)/9*8
                # - u/kariru2, Reddit
                kiMultiplier = (characterKit.eball_mod_max/24)*(12+special[2])
            kiATK = int(ATK * (kiMultiplier/100)) # Apply Ki multiplier
            print(f'{kiATK} (With {kiMultiplier}% Ki Multiplier)')
            
            print(f"Launching Super Attack: {special[0]} at {special[2]} Ki")
            calcATKSA(characterKit, special, kiATK, onAttackATK, 0, 0, "", crit, superEffective, additional, baseATK, activeATK)
        if special[2] < 12 and characterKit.rarity != 'LR':
            kiATK = int(ATK * (characterKit.eball_mod_max/100)) # Apply Ki multiplier
            print(f'{kiATK} (With {characterKit.eball_mod_max}% Ki Multiplier)')
            print(f"Launching Super Attack: {special[0]} at 12 Ki")
            calcATKSA(characterKit, special, kiATK, onAttackATK, 0, 0, "", crit, superEffective, additional, baseATK, activeATK)
        if special[2] < 18 and characterKit.rarity == 'LR':
            kiMultiplier = (((200-characterKit.eball_mod_mid)/12)*(18-12))+characterKit.eball_mod_mid
            kiATK = int(ATK * (kiMultiplier/100)) # Apply Ki multiplier
            print(f'{kiATK} (With {kiMultiplier}% Ki Multiplier)')
            print(f"Launching Super Attack: {special[0]} at 18 Ki")
            calcATKSA(characterKit, special, kiATK, onAttackATK, 0, 0, "", crit, superEffective, additional, baseATK, activeATK)
        if characterKit.rarity == "LR":
            kiATK = int(ATK * 2) # Apply Ki multiplier
            print(f'{kiATK} (With 200% Ki Multiplier)')
            print(f"Launching Super Attack: {special[0]} at 24 Ki")
            calcATKSA(characterKit, special, kiATK, onAttackATK, 0, 0, "", crit, superEffective, additional, baseATK, activeATK)
    else:
        if characterKit.finish_skills:
            print("No Super Attacks found")
            saPerBuff = 0
            saFlatBuff = 0
            atkBuff = characterKit.finish_skills[len(characterKit.finish_skills)-1].split('+')[1]
            if atkBuff.__contains__('%'):
                saPerBuff += int(atkBuff.split('%')[0])
            else:
                saFlatBuff += int(atkBuff.split(' ')[0])
            
            if characterKit.rarity == "LR":
                kiATK = int(ATK * 2) # Apply Ki multiplier
                print(f'{kiATK} (With 200% Ki Multiplier)')
            else:
                print(characterKit.eball_mod_max)
                kiATK = int(ATK * (characterKit.eball_mod_max/100)) # Apply Ki multiplier
                print(f'{kiATK} (With {characterKit.eball_mod_max}% Ki Multiplier)')
            
            ATK = int(ATK * (1 + (saPerBuff/100))) # Apply 'on attack' percentage buffs
            print(f"{ATK} (With {saPerBuff}% 'On Attack' Passive Buff)")
            ATK = int(ATK + saFlatBuff) # Apply 'on attack' flat buffs
            print(f"{ATK} (With {saFlatBuff} Flat 'On Attack' Passive Buff)")
            
            for finish_skill in characterKit.finish_skills[:-1]:
                finishMultiplier = 4 # Ferocious multiplier by default
                if characterKit.finish_skills[1].__contains__('super-intense damage'):
                    finishMultiplier = 5
                elif characterKit.finish_skills[1].__contains__('ultimate damage'):
                    finishMultiplier = 5.5
                elif characterKit.finish_skills[1].__contains__('super-ultimate damage'):
                    finishMultiplier = 7.5
                
                charge = 1
                if finish_skill[1].__contains__('charge count'):
                    atkBuff = finish_skill[1].split('by ')[1]
                    for i in range(0, 160, 10):
                        charge += ((int(atkBuff.split('%')[0])*i)/100)
                        if crit:
                            print(f"Finish Effect APT (With {i} Charge, {finishMultiplier}%): {str(int(ATK*charge*finishMultiplier))} (Crit: {str(int(ATK*charge*finishMultiplier*1.9))})")
                        elif superEffective:
                            print(f"Finish Effect APT (With {i} Charge, {finishMultiplier}%): {str(int(ATK*charge*finishMultiplier))} (Super Effective: {str(int(ATK*charge*finishMultiplier*1.5))})")
                        else:
                            print(f"Finish Effect APT (With {i} Charge, {finishMultiplier}%): {str(int(ATK*charge*finishMultiplier))}")
                else:
                    if crit:
                        print(f"Finish Effect APT ({finishMultiplier*100}%): {str(int(ATK*charge*finishMultiplier))} (Crit: {str(int(ATK*charge*finishMultiplier*1.9))})")
                    elif superEffective:
                        print(f"Finish Effect APT ({finishMultiplier*100}%): {str(int(ATK*charge*finishMultiplier))} (Super Effective: {str(int(ATK*charge*finishMultiplier*1.5))})")
                    else:
                        print(f"Finish Effect APT ({finishMultiplier*100}%): {str(int(ATK*charge*finishMultiplier))}")
        else:
            print("No Super Attacks found\n")

# Calculate ATK stat given 'on attack' conditions (When attacking, per attack
# evaded/received/performed, when the target enemy ..., etc.)
def calcATKSA(characterKit, special, ATK, onAttackATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK):
    copyATK = copy.copy(onAttackATK)
    
    if (copyATK.head != None):
        if (copyATK.head.data).__contains__('(up to once'):
            condition = f'({(copyATK.head.data).split("% (")[1]}'
        elif (copyATK.head.data).__contains__("' ("):
            condition = f'({(copyATK.head.data).split("% (")[1]}'
        elif (copyATK.head.data).__contains__(" (self"):
            condition = (copyATK.head.data)[(copyATK.head.data.find('(')):]
        else:
            condition = f'({(copyATK.head.data).split(" (")[1]}'
        buff = f'({(copyATK.head.data).split(" (")[0]}'
                
        if buff.__contains__('counter') or buff.__contains__('Counter'):
            counter = buff
            copyATK.removeLine()
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            return
        else:
            newSAPerBuff = saPerBuff
            newSAFlatBuff = saFlatBuff
            buff = buff.split("ATK ")[1]
        
            if (((copyATK.head.data).__contains__("(up to ") and
            not (copyATK.head.data).__contains__("(up to once within a turn")) or
            (copyATK.head.data).__contains__(", up to ")):
                limit = (copyATK.head.data).split("up to ")[1]
                if limit.__contains__('%'):
                    limit = int(limit.split("%)")[0])
                else:
                    limit = int(limit.split(")")[0])
            elif (copyATK.head.data).__contains__("(no more than "):
                limit = (copyATK.head.data).split("no more than ")[1]
                if limit.__contains__('%'):
                    limit = int(limit.split("%)")[0])
                else:
                    limit = int(limit.split(")")[0])
            
            flat = False
            if '%' not in buff:
                flat = True
            else:
                flat = False
                buff = buff.split("%")[0]
            
            if '+' in buff:
                buff = int(buff.split('+')[1])
            else:
                buff = -1*int(buff.split('-')[1])
            
            if flat:
                newSAFlatBuff += buff
            else:
                newSAPerBuff += buff
        
        copyATK.removeLine()
        
        if condition == "(When attacking)":
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif condition.__contains__("Once only") or condition.__contains__("once only"):
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
            print("ATK (After one-time buff):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif (condition.__contains__("After delivering a final blow") or
            condition.__contains__("a final blow is delivered")):
            print("ATK (Before delivering a final blow):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif (condition.__contains__("When attacking a") and
        condition.__contains__(" enemy")):
            print(f"ATK {condition}")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
            condition = condition.replace('When attacking a', 'When not attacking a')
            print(f"ATK {condition}")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif (condition.__contains__("When there is a") and
        condition.__contains__(" enemy")):
            print(f"ATK {condition}")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
            condition = condition.replace('When there is a', 'When there is not a')
            print(f"ATK {condition}")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("receiving an attack"):
            print("ATK (Before receiving an attack):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("receiving or evading an attack"):
            print("ATK (Before receiving or evading an attack):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("evading an attack"):
            print("ATK (Before evading an attack):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__('After guard is activated'):
            print('ATK (Before guard is activated):')
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            condition = condition.replace(', or ', ', for ')
            print(f'ATK {condition}:')
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif condition.__contains__('Whenever guard is activated'):
            if not condition.__contains__('(up to') and not "limit" in locals():
                limit = buff
            
            print(f'ATK (Before guard is activated):')
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            
            for i in range(1, int(limit/buff)+1):
                if i == 1:
                    print(f'ATK (Guard activated {i} time):')
                else:
                    print(f'ATK (Guard activated {i} times):')
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (buff*i), newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff + (buff*i), newSAFlatBuff])
        elif condition.__contains__('henever guard is activated'):
            limit = buff
            if condition.__contains__('(up to'):
                limit = condition.split('(up to ')[1]
                limit = int(limit.split('%')[0])
                print(limit/buff)
                   
            condition = condition.replace('are on the', 'are not on the')
            condition = condition.replace(condition[condition.find('whenever'):], '')
            print(f'ATK {condition}before guard is activated):')
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            
            condition = condition.replace('are not on the', 'are on the')
            for i in range(1, int(limit/buff)+1):
                if i == 1:
                    print(f'ATK {condition}guard activated {i} time:')
                else:
                    print(f'ATK {condition}guard activated {i} times:')
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (buff*i), newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff + (buff*i), newSAFlatBuff])
        elif condition.__contains__("he more HP remaining"):
            for i in range(0, 101):
                if i % 10 == 0:
                    print("ATK at " + str(i) + "% HP:")
                    if flat:
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff,  int(saFlatBuff + (int(buff)*(i/100))), counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff, int(saFlatBuff + (int(buff)*(i/100)))])
                    else:
                        calcATKSA(characterKit, special, ATK, copyATK, int(saPerBuff + (int(buff)*(i/100))), newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, int(saPerBuff + (int(buff)*(i/100))), saFlatBuff])
        elif condition.__contains__("For every ") and condition.__contains__(" Ki when attacking"):
            kiLimit = 1
            if not condition.__contains__('For every Ki when attacking'):
                kiLimit = condition.split('For every ')[1]
                kiLimit = int(kiLimit.split(' Ki when ')[0])
            if "limit" in locals():
                if limit/buff <= int(ki):
                    if flat:
                        newSAFlatBuff = saFlatBuff + limit
                    else:
                        newSAPerBuff = saPerBuff + limit
                    print(f"ATK (With 12 Ki):")
                    calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
                else:
                    print(f"ATK (Before performing {cond}):")
                    #calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                    #print(f"ATK (After performing {cond}):")
                    #calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            else:
                buff = buff*(ki/kiLimit)
                if flat:
                    newSAFlatBuff = saFlatBuff + (buff)
                else:
                    newSAPerBuff = saPerBuff + (buff)
                print(f'ATK (With {ki} Ki):')
                calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif condition.__contains__("For every Rainbow Ki Sphere obtained"):
            if flat:
                print("ATK (With 0 Rainbow Ki Spheres obtained):")
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*2.5), counter, crit, superEffective, additional, baseATK, activeATK)
                print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*5), counter, crit, superEffective, additional, baseATK, activeATK)
            else:
                print("ATK (With 0 Rainbow Ki Spheres obtained):")
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*2.5), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*5), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("or every "):
            cond = (condition.split('or every ')[1]).replace(',', '')
            if condition.__contains__(', for') and not condition.__contains__('ttack performed, for'):
                cond2 = condition.replace(', for every attack performed', '')
                cond2 = cond2.replace('hen there is', 'hen there is not')
                print(f"ATK {cond2}:")
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            elif not condition.__contains__('performed'):
                cond = cond.replace('ttack ', 'ttacks ')
                print(f'ATK (With 0 {cond}:')
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                cond = cond.replace('ttacks ', 'ttack ')
                
            if not "limit" in locals():
                if condition.__contains__('within the turn'):
                    for i in range(1, 16):
                        if i == 1:
                            print(f'ATK (With {str(i)} {cond}:')
                        else:
                            cond = cond.replace('ttack ', 'ttacks ')
                            print(f'ATK (With {str(i)} {cond}:')
                        if flat:
                            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff + (buff*i), counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, saFlatBuff + (buff*i)])
                        else:
                            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (buff*i), saFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff + (buff*i), newSAFlatBuff])
                else:
                    turnLimit = additional+2
                    if (special[1].__contains__('Raises ATK by') and
                    special[1].__contains__('% for ') and
                    special[1].__contains__(' turns ')):
                        turnLimit = special[1].split(' for ')[1]
                        turnLimit = int(turnLimit.split(' turns ')[0])
                        turnLimit = max((math.ceil(turnLimit/2))*(additional+1), 35)
                    
                    for i in range(1, turnLimit):
                        if i == 1:
                            print(f'ATK (With {str(i)} {cond}:')
                        else:
                            cond = cond.replace('ttack ', 'ttacks ')
                            print(f'ATK (With {str(i)} {cond}:')
                        if flat:
                            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff + (buff*i), counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff, saFlatBuff + (buff*i)])
                        else:
                            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (buff*i), saFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff + (buff*i), saFlatBuff])
            else:
                for i in range(1, int(limit/buff)+1):
                    if i == 1:
                        print(f'ATK (With {str(i)} {cond}):')
                    else:
                        cond = cond.replace('ttack ', 'ttacks ')
                        print(f'ATK (With {str(i)} {cond}):')
                    if flat:
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff + (buff*i), counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff, saFlatBuff + (buff*i)])
                    else:
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (buff*i), saFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff + (buff*i), saFlatBuff])
                if limit % buff != 0:
                    print(f'ATK (With {str(i+1)} {cond}):')
                    if flat:
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff + limit, counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff, saFlatBuff + limit])
                    else:
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + limit, saFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, saPerBuff + limit, saFlatBuff])
        elif (condition.__contains__(" there is another") and
        condition.__contains__("Category ally ")):
            category = condition.split("another '")[1]
            category = category.split("' Category")[0]
                
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, [activeATK, newSAPerBuff, newSAFlatBuff])
            
            condition = condition.replace('there is', 'there is not')
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("Category ally attacking in the same turn"):
            if condition.__contains__(' Per '):
                category = condition.split(" Per ")[1]
            else:
                category = condition.split(" per ")[1]
            category = category.split(" Category")[0]
                
            if condition.__contains__("self excluded"): 
                for i in range(0, 3):
                    print("ATK (When attacking, with " + str(i) + " " + category + " Category allies in the same turn):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (i * buff), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            else:
                for i in range(1, 4):
                    print("ATK (When attacking, with " + str(i) + " " + category + " Category allies in the same turn):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (i * buff), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("Starting from the ") and condition.__contains__(" turn from the "):
            turn = condition.replace('Starting from ', 'Before ')
            turn = turn.replace('chance', 'chance not activated')
            print(f"ATK {turn}:")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("turn(s)"):
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK (After turn buff):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("When the target enemy is "):
            condition = condition.replace("{passiveImg:atk_down}", "ATK Down")
            condition = condition.replace("{passiveImg:def_down}", "DEF Down")
            condition = condition.replace("{passiveImg:stun}", "Stunned")
            condition = condition.replace("{passiveImg:astute}", "Sealed")
            
            print("ATK (Without status condition):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("After performing ") and (condition.__contains__("ttack(s) in battle") or
        condition.__contains__("ttacks in battle")):
            cond = condition.split("After performing ")[1]
            
            print(f"ATK (Before performing {cond}):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK (After performing {cond}):")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("Every time the character performs ") and condition.__contains__("ttacks in battle"):
            cond = condition.split("Every time the character performs ")[1]
            
            print(f"ATK (Before performing {cond.split(',')[0]}):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK (For every {cond.replace('attacks', 'attacks performed')}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif (condition.__contains__("After receiving ") and 
        (condition.__contains__("ttacks in battle") or condition.__contains__("ttack(s) in battle"))):
            cond = condition.split("After receiving ")[1]
            
            print(f"ATK (Before receiving {cond}):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK (After receiving {cond}):")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)        
        elif condition.__contains__("After evading ") and condition.__contains__("ttacks in battle"):
            cond = condition.split("After evading ")[1]
            
            print(f"ATK (Before evading {cond}):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK (After evading {cond}):")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("For every Ki when attacking"):
            if limit/buff <= special[2]:
                if flat:
                    newSAFlatBuff = saFlatBuff + limit
                else:
                    newSAPerBuff = saPerBuff + limit
                print(f"ATK (With 12 Ki):")
                calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            else:
                print(f"ATK (Before performing {cond}):")
                #calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                #print(f"ATK (After performing {cond}):")
                #calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__(" your team has ") and condition.__contains__("attacking in the same turn"):
            cond = condition.split(" your team has ")[0]
            ally = condition.split("your team has ")[1]
            
            print(f"ATK ({cond} your team has {ally}):")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            print(f"ATK ({cond} your team doesn't have {ally}):")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif (condition.__contains__("Per ") and condition.__contains__(" ally on the team")):
            category = condition.split("Per ")[1]
            category = category.split(" ally on")[0]
            
            limitLoop = 8
            if "limit" in locals(): # WE SAIYANS-
                limitLoop = int(limit/buff)+1
            for i in range(1, limitLoop):
                if i == 1:
                    print(f'ATK (With {str(i)} {category} ally on the team):')
                else:
                    category = category.replace('ally', 'allies')
                    print(f'ATK (With {str(i)} {category} allies on the team):')
                if flat:
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff + (i * buff), counter, crit, superEffective, additional, baseATK, activeATK)
                else:
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff + (i * buff), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif (condition.__contains__("When there is a")):
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            condition = condition.replace('When there is a', 'When there is not a')
            condition = condition.replace('when attacking with', 'when not attacking with')
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("per Ki Sphere obtained"):
            condition = condition.split(', per')[0]
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*3), counter, crit, superEffective, additional, baseATK, activeATK)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*7.5), counter, crit, superEffective, additional, baseATK, activeATK)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK {condition}, with 23 (Max) Ki Spheres Obtained):")
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*23), counter, crit, superEffective, additional, baseATK, activeATK)
                    print(f"ATK {condition}, with {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                else:
                    print(f"ATK {condition}, with {3 + kiStart} Ki Spheres Obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*3), counter, crit, superEffective, additional, baseATK, activeATK)
                    print(f"ATK {condition}, with {7.5 + kiStart} (AVG) Ki Spheres obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*7.5), counter, crit, superEffective, additional, baseATK, activeATK)
                    print(f"ATK {condition}, with {23 - kiStart} (Max) Ki Spheres obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff+(buff*23), counter, crit, superEffective, additional, baseATK, activeATK)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*3), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*7.5), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK {condition}, with 23 (Max) Ki Spheres Obtained):")
                        calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*23), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                    print(f"ATK {condition}, with {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                else:
                    print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*3), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                    print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*7.5), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
                    print(f"ATK {condition}, with 23 (Max) Ki Spheres obtained):")
                    calcATKSA(characterKit, special, ATK, copyATK, saPerBuff+(buff*23), saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        elif condition.__contains__("When attacking with ") and condition.__contains__(" Ki"):
            kiATK = condition.split("When attacking with ")[1]
            kiATK = int(kiATK.split(" ")[0])
            if ((condition.__contains__("or more") and special[2] < kiATK) or
            (condition.__contains__("or less") and special[2] > kiATK)):
                calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
            else:
                print(f"ATK {condition}:")
                calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
        else:
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
    
            condition = condition.replace('when there is ', 'when there is not ')
            condition = condition.replace('are on the ', 'are not on the ')
            condition = condition.replace('when attacking', 'when not attacking')
            condition = condition.replace('great chance', 'without RNG chance')
            condition = condition.replace('Great chance', 'Without RNG chance')
            condition = condition.replace(' HP is ', ' HP is not ')
            condition = condition.replace('As the ', 'Not as the ')
            condition = condition.replace('hen facing ', 'hen not facing ')
            condition = condition.replace(' obtained', ' not obtained')
            condition = condition.replace(' turn are', ' turn are not')
            
            if condition.__contains__('Activates the Entrance Animation'):
                condition = "(Without Entrance buff)"
            
            print(f"ATK {condition}:")
            calcATKSA(characterKit, special, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, baseATK, activeATK)
    else:
        ATK = int(ATK * (1 + (saPerBuff/100))) # Apply 'on attack' percentage buffs
        print(f"{ATK} (With {saPerBuff}% 'On Attack' Passive Buff)")
        ATK = int(ATK + saFlatBuff) # Apply 'on attack' flat buffs
        print(f"{ATK} (With {saFlatBuff} Flat 'On Attack' Passive Buff)")
        
        baseATK = int(baseATK * (1 + (saPerBuff/100))) # Apply 'on attack' percentage buffs
        baseATK = int(baseATK + saFlatBuff) # Apply 'on attack' flat buffs
        
        stack = False
        turnLimit = 0
        
        ATKmultiplier = 0
        SAmultiplier = 2.6 # Damage by default
        for line in special[1].split('\n'):
            if line.__contains__('ATK') and not line.__contains__('lowers ATK'):
                buff = line.split('by ')[1]
                ATKmultiplier += int(buff.split('%')[0])/100
                
                if line.split('ATK')[1].__contains__('turn'):
                    turnLimit = line.split('% for ')[1]
                    turnLimit = int(turnLimit.split(' turn')[0])
                else:
                    stack = True
                    
            elif line.__contains__("low damage"):
                SAmultiplier = 2.2
            elif line.__contains__("huge damage") or line.__contains__("destructive damage"):
                if characterKit.card_links.__contains__('Super Strike'):
                    SAmultiplier = 3.4
                elif characterKit.rarity == 'LR':
                    if special[0].__contains__('(Extreme)'):
                        SAmultiplier = 4.4
                    else:
                        SAmultiplier = 3.9
                elif special[0].__contains__('(Extreme)'):
                    SAmultiplier = 3.4
                else:
                    SAmultiplier = 2.9
            elif line.__contains__("extreme damage") or line.__contains__("mass damage"):
                if characterKit.card_links.__contains__('Super Strike') or special[0].__contains__('(Extreme)'):
                    SAmultiplier = 4.3
                else:
                    SAmultiplier = 3.55
            elif line.__contains__("supreme damage"):
                if characterKit.card_links.__contains__('Super Strike'):
                    if special[0].__contains__("(Extreme)"):
                        SAmultiplier = 6.3
                    else:
                        SAmultiplier = 5.3
                elif special[0].__contains__("(Extreme)"):
                    SAmultiplier = 5.3
                else:
                    SAmultiplier = 4.3
            elif line.__contains__("immense damage"):
                if special[0].__contains__("(Extreme)"):
                    SAmultiplier = 6.3
                else:
                    SAmultiplier = 5.05
            elif line.__contains__("mega-colossal damage"):
                if special[0].__contains__("(Extreme)"):
                    SAmultiplier = 5.9
                else:
                    SAmultiplier = 5.4
            elif line.__contains__("colossal damage"):
                if special[0].__contains__("(Extreme)"):
                    SAmultiplier = 4.2
                else:
                    SAmultiplier = 3.95
        
        if len(special) > 3:
            if (special[3].__contains__("Super Attack power +") or
                special[3].__contains__("Super Attack +")):
                specialPower = special[3].split("+")[1]
                SAmultiplier += int(specialPower.split("%")[0])/100
                special = tuple([special[0], special[1], special[2]])
        
        baseATKmultiplier = 0
        baseSAmultiplier = 2.6
        for line in characterKit.specials[0][1].split('\n'):
            if line.__contains__('ATK') and not line.__contains__('lowers ATK'):
                buff = line.split('by ')[1]
                baseATKmultiplier += int(buff.split('%')[0])/100
            elif line.__contains__("low damage"):
                baseSAmultiplier = 2.2
            elif line.__contains__("huge damage") or line.__contains__("destructive damage"):
                baseSAmultiplier = 2.9
            elif line.__contains__("extreme damage") or line.__contains__("mass damage"):
                baseSAmultiplier = 3.55
            elif line.__contains__("supreme damage"):
                if characterKit.specials[0][0].__contains__("(Extreme)"):
                    baseSAmultiplier = 5.3
                else:
                    baseSAmultiplier = 4.3
            elif line.__contains__("immense damage"):
                if characterKit.specials[0][0].__contains__("(Extreme)"):
                    baseSAmultiplier = 6.3
                else:
                    baseSAmultiplier = 5.05
            elif line.__contains__("mega-colossal damage"):
                if characterKit.specials[0][0].__contains__("(Extreme)"):
                    baseSAmultiplier = 5.9
                else:
                    baseSAmultiplier = 5.4
            elif line.__contains__("colossal damage"):
                if characterKit.specials[0][0].__contains__("(Extreme)"):
                    baseSAmultiplier = 4.2
                else:
                    baseSAmultiplier = 3.95
            
        if len(characterKit.specials[0]) > 3:
            if (characterKit.specials[0][3].__contains__("Super Attack power +") or
                characterKit.specials[0][3].__contains__("Super Attack +")):
                specialPower = characterKit.specials[0][3].split("+")[1]
                baseSAmultiplier += int(specialPower.split("%")[0])/100
                characterKit.specials[0] = tuple([characterKit.specials[0][0], characterKit.specials[0][1], characterKit.specials[0][2]])
        
        if (special[1].__contains__('critical hit') or
        characterKit.specials[0][1].__contains__('critical hit')):
            crit = True
        elif special[1].__contains__('attacks effective against all Types'):
            superEffective = True
                
        # Adds HiPo SA boost for SSR/UR/LR characters
        if stack:
            if characterKit.rarity == 'SSR' or characterKit.rarity == 'UR' or characterKit.rarity == 'LR':
                print(f'Stacks ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier + 15 (.75%) HiPo SA Boost')
                SAmultiplier += .75
                baseSAmultiplier += .75
            else:
                print(f'Stacks ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier')
        else:
            if characterKit.rarity == 'SSR' or characterKit.rarity == 'UR' or characterKit.rarity == 'LR':
                print(f'Raises ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier + 15 (.75%) HiPo SA Boost')
                SAmultiplier += .75
                baseSAmultiplier += .75
            else:
                print(f'Raises ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier')
        
        counterPower = 0
        if counter != "":
            if counter.__contains__("enormous power"):
                counterPower = 2
            elif counter.__contains__("tremendous power"):
                counterPower = 3
            elif counter.__contains__("ferocious power"):
                counterPower = 4
        
        if len(special) > 3:
            if special[3].__contains__("Super Attack Transformation"):
                # Dev Note: Why do 'more power' and 'even more power' mean the same thing?
                # TBF this is just for the goten/trunks/marron F2P card's pre and post=eza
                # kit, respectively, but... yeah.
                transPower = .2
                if special[3].__contains__('greater power'):
                    transPower = .6
                elif special[3].__contains__('supremely boosted'):
                    turnLimit = special[3].split('boosted for ')[1]
                    turnLimit = int(turnLimit.split(' turns')[0])
                    if turnLimit < 2:
                        turnLimit = additional
                        if characterKit.rarity == "SSR" or characterKit.rarity == "UR" or characterKit.rarity == "LR":
                            turnLimit = 2 + additional
                    else:
                        turnLimit = (math.ceil(turnLimit/2))*(additional+1) + 1
                    
                    for i in range(0, turnLimit):
                        if i == 0:
                            if crit:
                                print(f"Super Attack APT (0 Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.9))})")
                            elif superEffective:
                                print(f"Super Attack APT (0 Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.5))})")
                            else:
                                print(f"Super Attack APT (0 Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))}")
                        else:
                            if crit:
                                print(f"Super Attack APT ({str(i)} Transformed Stack (90%)): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(.9*i))))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(.9*i))*1.9))})")
                            elif superEffective:
                                print(f"Super Attack APT ({str(i)} Transformed Stack (90%)): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(.9*i))))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(.9*i))*1.5))})")
                            else:
                                print(f"Super Attack APT ({str(i)} Transformed Stack (90%)): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(.9*i))))}")
                    return
                
                if turnLimit < 2:
                    turnLimit = additional
                    if characterKit.rarity == "SSR" or characterKit.rarity == "UR" or characterKit.rarity == "LR":
                        turnLimit = 2 + additional
                else:
                    turnLimit = (math.ceil(turnLimit/2))*(additional+1) + 1
                
                for i in range(1, turnLimit):
                    if crit:
                        print(f"Super Attack APT ({i} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.9))})")
                    elif superEffective:
                        print(f"Super Attack APT ({i} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.5))})")
                    else:
                        print(f"Super Attack APT ({i} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))}")
                    
                SAmultiplier += transPower
                for i in range(1, turnLimit):
                    if crit:
                        print(f"Transformed Super Attack APT ({i} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.9))})")
                    elif superEffective:
                        print(f"Transformed Super Attack APT ({i} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.5))})")
                    else:
                        print(f"Transformed Super Attack APT ({i} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))}")
        elif stack:
            if special[1].__contains__('chance of raising ATK'):
                if crit:
                    print("Super Attack APT (Without RNG chance): " + str(int(ATK*(SAmultiplier))) 
                        + " (Crit: " + str(int(int(ATK*(ATKmultiplier+SAmultiplier)))*1.9) + ")")
                elif superEffective:
                    print("Super Attack APT (Without RNG chance): " + str(int(ATK*(SAmultiplier))) 
                    + " (Super Effective: " + str(int(int(ATK*(ATKmultiplier+SAmultiplier)))*1.5) + ")")
                else:
                    print("Super Attack APT (Without RNG chance): " + str(int(ATK*(SAmultiplier))))
            
            # Dev Note: Fix turn limit for stacks (3 turns + UR + no passive additionals
            # only printing 3 stacks, should print 4)
            # Dev Note: Fix stacking for units with multiple SAs, and if some of those SAs stack
            # (STR Perfect Cell, LRs, etc.)
            if turnLimit < 2:
                turnLimit = additional
                if characterKit.rarity == "SSR" or characterKit.rarity == "UR" or characterKit.rarity == "LR":
                    turnLimit = 2 + additional
            else:
                turnLimit = (math.ceil(turnLimit/2))*(additional+1)
            
            ATKmultiplier2 = ATKmultiplier
            mainStack = 0
            baseATKmultiplier2 = baseATKmultiplier
            baseStack = 0
            for i in range(1, turnLimit):
                if not characterKit.specials[0][2] == special[2]:
                    if i > 1 and math.ceil(((turnLimit - i) / (additional + 1)) % additional) == 0:
                        baseATKmultiplier2 += baseATKmultiplier
                        stackATK = int(baseATK*(baseATKmultiplier2+ATKmultiplier2+baseSAmultiplier))
                        baseStack += 1
                        
                        if crit:
                            print(f"Super Attack APT ({str(baseStack)} Stack, at {characterKit.specials[0][2]} Ki): {str(stackATK)} (Crit: {str(int(stackATK*1.9))})")
                        elif superEffective:
                            print(f"Super Attack APT ({str(baseStack)} Stack, at {characterKit.specials[0][2]} Ki): {str(stackATK)} (Super Effective: {str(int(stackATK*1.5))})")
                        else:
                            print(f"Super Attack APT ({str(baseStack)} Stack, at {characterKit.specials[0][2]} Ki): {str(stackATK)}")
                    else:
                        if mainStack != 0:
                            ATKmultiplier2 += ATKmultiplier
                        stackATK = int(baseATK*(baseATKmultiplier2+ATKmultiplier2+baseSAmultiplier))
                        mainStack += 1
                        
                        if crit:
                            print(f"Super Attack APT ({str(mainStack)} Stack, at {special[2]} Ki): {str(stackATK)} (Crit: {str(int(stackATK*1.9))})")
                        elif superEffective:
                            print(f"Super Attack APT ({str(mainStack)} Stack, at {special[2]} Ki): {str(stackATK)} (Super Effective: {str(int(stackATK*1.5))})")
                        else:
                            print(f"Super Attack APT ({str(mainStack)} Stack, at {special[2]} Ki): {str(stackATK)}")
                else:
                    ATKmultiplier2 += ATKmultiplier
                    stackATK = int(ATK*(ATKmultiplier2+SAmultiplier))
                    mainStack += 1
                    
                    if crit:
                        print("Super Attack APT (" + str(mainStack) + " Stack): " + str(stackATK) 
                        + " (Crit: " + str(int(stackATK*1.9)) + ")")
                    elif superEffective:
                        print("Super Attack APT (" + str(mainStack) + " Stack): " + str(stackATK) 
                        + " (Super Effective: " + str(int(stackATK*1.5)) + ")")
                    else:
                        print("Super Attack APT (" + str(mainStack) + " Stack): " + str(stackATK))
        elif additional != 0:            
            if special[1].__contains__('chance of raising ATK'):
                if crit:
                    print("Super Attack APT (Without RNG chance): " + str(int(ATK*(SAmultiplier))) 
                        + " (Crit: " + str(int(int(ATK*(ATKmultiplier+SAmultiplier)))*1.9) + ")")
                elif superEffective:
                    print("Super Attack APT (Without RNG chance): " + str(int(ATK*(SAmultiplier))) 
                    + " (Super Effective: " + str(int(int(ATK*(ATKmultiplier+SAmultiplier)))*1.5) + ")")
                else:
                    print("Super Attack APT (Without RNG chance): " + str(int(ATK*(SAmultiplier))))
            
            if turnLimit < 2:
                turnLimit = additional
                if characterKit.rarity == "SSR" or characterKit.rarity == "UR" or characterKit.rarity == "LR":
                    turnLimit = 2 + additional
            else:
                turnLimit = (math.ceil(turnLimit/2))*(additional+1) + 1
            
            for i in range(1, turnLimit):
                if not characterKit.specials[0][2] == special[2] and i > 1:
                    stackATK = int(baseATK*((baseATKmultiplier*i)+ATKmultiplier+baseSAmultiplier))
                    
                    if crit:
                        print(f"Super Attack APT ({str(i)} Stack, at {characterKit.specials[0][2]} Ki): {str(stackATK)} (Crit: {str(int(stackATK*1.9))})")
                    elif superEffective:
                        print(f"Super Attack APT ({str(i)} Stack, at {characterKit.specials[0][2]} Ki): {str(stackATK)} (Super Effective: {str(int(stackATK*1.5))})")
                    else:
                        print(f"Super Attack APT ({str(i)} Stack, at {characterKit.specials[0][2]} Ki): {str(stackATK)}")
                else:
                    stackATK = int(ATK*((ATKmultiplier*i)+SAmultiplier))
                    
                    if crit:
                        print("Super Attack APT (" + str(i) + " Stack): " + str(stackATK) 
                        + " (Crit: " + str(int(stackATK*1.9)) + ")")
                    elif superEffective:
                        print("Super Attack APT (" + str(i) + " Stack): " + str(stackATK) 
                        + " (Super Effective: " + str(int(stackATK*1.5)) + ")")
                    else:
                        print("Super Attack APT (" + str(i) + " Stack): " + str(stackATK))
        else:
            finalATK = int(ATK*(SAmultiplier+ATKmultiplier))
            if crit:
                print("Super Attack APT: " + str(finalATK) + " (Crit: " + str(int(finalATK*1.9)) + ")")
            elif superEffective:
                print("Super Attack APT: " + str(finalATK) + " (Super Effective: " + str(int(finalATK*1.5)) + ")")
            else:
                print("Super Attack APT: " + str(finalATK))
                        
        if counterPower != 0:
            if crit:
               print(f"Counter APT (Before SA, With {counterPower*100}% Multiplier): " + str(int(ATK*counterPower)) + 
               " (Crit: " + str(int(ATK*counterPower*1.9)) + ")")
                        
               for i in range(1, turnLimit):
                  print(f"Counter APT (After SA {i}, With {counterPower*100}% Multiplier): " + str(int(ATK*(counterPower+(ATKmultiplier*i)))) + 
                  " (Crit: " + str(int(ATK*(counterPower+(ATKmultiplier*i))*1.9)) + ")")
            elif superEffective:
               print(f"Counter APT (Before SA, With {counterPower*100}% Multiplier): " + str(int(ATK*counterPower)) + 
               " (Super Effective: " + str(int(ATK*counterPower*1.5)) + ")")
                     
               for i in range(1, turnLimit):
                  print(f"Counter APT (After SA {i}, With {counterPower*100}% Multiplier): " + str(int(ATK*(counterPower+(ATKmultiplier*i)))) + 
                  " (Super Effective: " + str(int(ATK*(counterPower+(ATKmultiplier*i))*1.5)) + ")")
            else:
               print(f"Counter APT (Before SA, With {counterPower*100}% Multiplier): {str(int(ATK*counterPower))}")
                 
               for i in range(1, turnLimit):
                  print(f"Counter APT (After SA {i}, With {counterPower*100}% Multiplier): {str(int(ATK*(counterPower+(ATKmultiplier*i))))}")   
        
        if characterKit.active_skill_effect.__contains__('damage to '):
            if type(activeATK) != int:
                if type(activeATK[0]) == list:
                    activeATK[0] = activeATK[0][0]
            
            active_skill_multiplier = 550
            if characterKit.active_skill_effect.__contains__('mega-colossal damage'):
                active_skill_multiplier = 440
            elif (characterKit.active_skill_effect.__contains__('aises ATK by ') and
            characterKit.active_skill_effect.__contains__('% temporarily then causes damage to enemy')):
                mult = characterKit.active_skill_effect.split('aises ATK by ')[1]
                active_skill_multiplier = int(mult.split('% temp')[0])
                
            if characterKit.active_skill_effect.__contains__('assively raises ATK temporarily'):
                active_skill_multiplier += 100
            elif characterKit.active_skill_effect.__contains__('reatly raises ATK temporarily'):
                active_skill_multiplier += 50
            elif (characterKit.active_skill_effect.__contains__('raises ATK by ') or
            characterKit.active_skill_effect.__contains__("raises allies' ATK by ")):
                active_skill_multiplier += int((characterKit.active_skill_effect.split('by ')[1]).split('%')[0])
            elif characterKit.active_skill_effect.__contains__('aises ATK temporarily'):
                active_skill_multiplier += 30
            
            if type(activeATK) != int:
                activeATK = int(int(activeATK[0] * (1 + (int(activeATK[1]/100)))) + activeATK[2])
            if turnLimit > 1 and stack:
                for i in range (1, turnLimit):
                    stackATK = int(activeATK*((ATKmultiplier*i)+(active_skill_multiplier/100)))
                    if crit:
                        print(f'Active Skill APT ({i} Stack, {active_skill_multiplier}%): {stackATK} (Crit: {int(stackATK*1.9)})')
                    elif superEffective:
                        print(f'Active Skill APT ({i} Stack, {active_skill_multiplier}%): {stackATK} (Super Effective: {int(stackATK*1.5)})')
                    else:
                        print(f'Active Skill APT ({i} Stack, {active_skill_multiplier}%): {stackATK}')
            else:
                activeATK = int(activeATK*(active_skill_multiplier/100))
                if crit:
                    print(f'Active Skill APT ({active_skill_multiplier}%): {activeATK} (Crit: {int(activeATK*1.9)})')
                elif superEffective:
                    print(f'Active Skill APT ({active_skill_multiplier}%): {activeATK} (Super Effective: {int(activeATK*1.5)})')
                else:
                    print(f'Active Skill APT ({active_skill_multiplier}%): {activeATK}')
                    
        if characterKit.finish_skills:
            # Removing buffs then recalculating with finish skill passive buff
            # 'When the Finish Effect is activated'
            ATK -= saFlatBuff
            ATK /= (1 + (saPerBuff/100))
            
            atkBuff = characterKit.finish_skills[len(characterKit.finish_skills)-1].split('+')[1]
            if atkBuff.__contains__('%'):
                saPerBuff += int(atkBuff.split('%')[0])
            else:
                saFlatBuff += int(atkBuff.split(' ')[0])
            
            ATK = int(ATK * (1 + (saPerBuff/100))) # Apply 'on attack' percentage buffs
            print(f"{ATK} (With {saPerBuff}% Finish Skill Buff)")
            ATK = int(ATK + saFlatBuff) # Apply 'on attack' flat buffs
            print(f"{ATK} (With {saFlatBuff} Flat Finish Skill Buff)")
            
            for finish_skill in characterKit.finish_skills[:-1]:
                finishMultiplier = 4 # Ferocious multiplier by default
                if characterKit.finish_skills[1].__contains__('super-intense damage'):
                    finishMultiplier = 5
                elif characterKit.finish_skills[1].__contains__('ultimate damage'):
                    finishMultiplier = 5.5
                elif characterKit.finish_skills[1].__contains__('super-ultimate damage'):
                    finishMultiplier = 7.5
                
                for i in range(0, turnLimit):
                    if i == 0:
                        if crit:
                            print(f"Finish Effect APT (With {i} Super Attack, {finishMultiplier*100}%): {str(int(ATK*finishMultiplier))} (Crit: {str(int(ATK*finishMultiplier*1.9))})")
                        elif superEffective:
                            print(f"Finish Effect APT (With {i} Super Attack, {finishMultiplier*100}%): {str(int(ATK*finishMultiplier))} (Super Effective: {str(int(ATK*finishMultiplier*1.9))})")
                        else:
                            print(f"Finish Effect APT (With {i} Super Attack, {finishMultiplier*100}%): {str(int(ATK*finishMultiplier))}")
                    else:
                        if crit:
                            print(f"Finish Effect APT (With {i} Super Attack, {finishMultiplier*100}%): {str(int(ATK*(1+ATKmultiplier+(baseATKmultiplier*i))*finishMultiplier))} (Crit: {str(int(ATK*(1+ATKmultiplier+(baseATKmultiplier*i))*finishMultiplier*1.9))})")
                        elif superEffective:
                            print(f"Finish Effect APT (With {i} Super Attack, {finishMultiplier*100}%): {str(int(ATK*(1+ATKmultiplier+(baseATKmultiplier*i))*finishMultiplier))} (Super Effective: {str(int(ATK*(1+ATKmultiplier+(baseATKmultiplier*i))*finishMultiplier*1.5))})")
                        else:
                            print(f"Finish Effect APT (With {i} Super Attack, {finishMultiplier*100}%): {str(int(ATK*(1+ATKmultiplier+(baseATKmultiplier*i))*finishMultiplier))}")
        print()

def calcATKCond(characterKit, condSoTATK, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount):
    copyCond = copy.copy(condSoTATK)
    
    if (condSoTATK.head != None):
        if (condSoTATK.head.data).__contains__('ATK -'):
            buff = '-' + (copyCond.head.data).split("ATK -")[1]
        else:
            buff = (copyCond.head.data).split("ATK +")[1]
        buff = buff.split(" (")[0]
        
        condition = (copyCond.head.data)[(copyCond.head.data).find('('):]
        if not condition.__contains__(')'):
            condition += ')'
        
        if (condSoTATK.head.data).__contains__("(up to "):
            limit = (condSoTATK.head.data).split("(up to ")[1]
            limit = int(limit.split("%)")[0])
        elif (condSoTATK.head.data).__contains__(", up to "):
            limit = (condSoTATK.head.data).split(", up to ")[1]
            limit = int(limit.split("%")[0])
        elif (condSoTATK.head.data).__contains__("(no more than "):
            limit = (condSoTATK.head.data).split("no more than ")[1]
            limit = int(limit.split("%)")[0])

        flat = False
        newPerBuff = atkPerBuff
        newFlatBuff = atkFlatBuff
        if '%' not in buff.split(' ')[0]:
            flat = True
            buff = buff.split(' ')[0]
            newFlatBuff += int(buff)
        else:
            flat = False
            buff = buff.split('%')[0]
            newPerBuff += int(buff)
        
        copyCond.removeLine()
        
        if condition.__contains__(", per Ki Sphere obtained"):
            cond1 = condition.split(', per')[0]            
            cond1 = cond1.replace('When there is ', 'When there is not ')
            cond1 = cond1.replace('in the same turn are ', 'in the same turn are not ')
            cond1 = cond1.replace(' Ki Spheres obtained', ' Ki Spheres not obtained')
            cond1 = cond1.replace('When HP is', 'When HP is not')
            print(f"ATK {cond1}):")
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            
            cond1 = cond1.replace('When there is not ', 'When there is ')
            cond1 = cond1.replace('in the same turn are not', 'in the same turn are')
            cond1 = cond1.replace(' Ki Spheres not obtained', ' Ki Spheres obtained')
            cond1 = cond1.replace('When HP is not', 'When HP is')
            if flat:
                if "limit" in locals():
                    print(f"ATK {cond1}, with {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (int(limit) * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK {cond1}, with 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK {cond1}, with 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK {cond1}, with 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                if "limit" in locals():
                    print(f"ATK {cond1}, with {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (int(limit)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK {cond1}, with 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK {cond1}, with 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK {cond1}, with 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("For every Ki Sphere obtained, per "):
            category = condition.split(', per ')[1].replace(' (self excluded))', '')
            for i in range(0, 3):
                if flat:
                    print(f"ATK (With {i} {category}, 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {i} {category}, 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {i} {category}, 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK (With {i} {category}, 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {i} {category}, 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {i} {category}, 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("For every Ki Sphere obtained with "):
            kiStart = condition.split('obtained with ')[1]
            kiStart = int(kiStart.split(' or ')[0])
            print(f"ATK (With less than {kiStart} Ki Spheres Obtained):")
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK (With {3 + kiStart} Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {7.5 + kiStart} (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {23 - kiStart} (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + ((23 - kiStart) * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("For every Ki Sphere obtained"):
            cond2 = ''
            if condition.__contains__('when there is'):
                cond2 = 'When there is not' + (condition.split('when there is')[1])[:-1]
                print(f"ATK ({cond2}):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                cond2 = cond2.replace('When there is not', ', when there is')
            
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, 3, enemyCount)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, 7.5, enemyCount)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, 23, enemyCount)
        elif condition.__contains__("For every Rainbow Ki Sphere obtained"):
            print("ATK (With 0 Rainbow Ki Spheres obtained):")
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) >= 2.5:
                        print(f"ATK (With 2.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (2.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 5:
                        print(f"ATK (With 5 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (2.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount) 
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) >= 2.5:
                        print(f"ATK (With 2.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (2.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 5:
                        print(f"ATK (With 5 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print("ATK (With 0 Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (2.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("For every ") and condition.__contains__(" Ki Sphere obtained"):
            kiType = (condition.split('For every ')[1]).split(' Ki Sphere')[0]
            if flat:
                print(f"ATK (With 0 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                print(f"ATK (With 3 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                print(f"ATK (With 7.5 (AVG) {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                print(f"ATK (With 23 (Max) {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                print(f"ATK (With 0 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                print(f"ATK (With 3 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                print(f"ATK (With 7.5 (AVG) {kiType} Ki Spheres obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                print(f"ATK (With 23 (Max) {kiType} Ki Spheres obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__(", per ") and condition.__contains__(" Ki Sphere obtained"):
            kiType = (condition.split('per ')[1]).split(' Ki Sphere')[0]
            condition = condition.split(', per')[0]
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK (With {3 + kiStart} Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {7.5 + kiStart} (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {23 - kiStart} (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + ((23 - kiStart) * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK {condition}, with 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__(" or more Ki Spheres obtained"):
            ki = int(condition[1:].split(' or more Ki Spheres obtained')[0])
            if ki <= kiObtained:
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)   
            else:
                condition = condition.replace(' obtained', ' not obtained')
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("Starting from the ") and condition.__contains__(" turn "):
            turn = condition.split('Starting from the ')[1]
            print(f'ATK (Before the {turn}:')
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            
            print(f'ATK {condition}:')
            activeCondATK = [newPerBuff, newFlatBuff]
            calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif ((condition.__contains__("turn(s) from the character's entry turn") or
        condition.__contains__("turns from the character's entry turn")) and not
        condition.__contains__('On the ')):
            turn = (condition.split('For ')[1]).split(' turn')[0]
            activeCondATK = [newPerBuff, newFlatBuff]
            print(f"ATK {condition}:")
            calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            
            activeCondATK = [atkPerBuff, atkFlatBuff]
            print(f"ATK (After {turn} turn buff):")
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif (condition.__contains__(" per ") and condition.__contains__(" ally on the team")):
            category = condition.split(" per ")[1]
            category = category.split(" ally")[0]
            
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1
            for i in range(0, limitLoop):
                if i == 1:
                    print(f'ATK (With {str(i)} {category} ally on the team):')
                else:
                    print(f'ATK (With {str(i)} {category} allies on the team):')
                if flat:
                    activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                    calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("Per ") and condition.__contains__(" ally on the team"):
            category = condition.split("Per ")[1]
            category = category.split(" ally")[0]
            
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1
            if condition.__contains__('self excluded'):
                for i in range(0, limitLoop):
                    if i == 0:
                        print(f'ATK (With no other {category} allies on the team):')
                    elif i == 1:
                        print(f'ATK (With another {category} ally on the team):')
                    else:
                        print(f'ATK (With {str(i)} {category} allies on the team):')
                    if flat:
                        activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                for i in range(1, limitLoop):
                    if i == 1:
                        print(f'ATK (With {str(i)} {category} ally on the team):')
                    else:
                        print(f'ATK (With {str(i)} {category} allies on the team):')
                    if flat:
                        activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif (condition.__contains__("Per ") and condition.__contains__(" Category ally attacking in the same turn")):
            category = condition.split("Per ")[1]
            category = category.split(" Category")[0]
            
            found = False
            for category2 in characterKit.categories:
                if category2 in condition:
                    found = True
                    break
            
            if condition.__contains__("self excluded") or found == False:
                for i in range(0, 3):
                    if i == 0:
                        print("ATK (With no other " + category + " Category allies attacking in the same turn):")
                    elif i == 1:
                        print("ATK (With another " + category + " Category ally attacking in the same turn):")
                    else:
                        print("ATK (With another " + str(i) + " " + category + " Category allies attacking in the same turn):")
                    if flat:
                        activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                for i in range(1, 4):
                    if i == 0:
                        print("ATK (With no other " + category + " Category ally attacking in the same turn):")
                    elif i == 1:
                        print("ATK (With " + str(i) + " " + category + " Category ally attacking in the same turn):")
                    else:
                        print("ATK (With " + str(i) + " " + category + " Category allies attacking in the same turn):")
                    if flat:
                        activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif (condition.__contains__("If the character's Ki is ")):
            activeCondATK = [newPerBuff, newFlatBuff]
            print(f"ATK {condition}:")
            calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)        
        elif (condition.__contains__("er existing enemy")):
            startLoop = 1
            limitLoop = 8
            if condition.__contains__('count starts from the '):
                startLoop = condition.split('count starts from the ')[1]
                startLoop = int((startLoop.split(' enemy')[0])[:-2])
                if enemyCount < startLoop and enemyCount != 0:
                    print(f'ATK (When facing less than {str(startLoop)} enemies):')
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    if enemyCount == 0:
                        print(f'ATK (When facing {str(startLoop)} or more enemies):')
                        for i in range(startLoop, limitLoop):
                            if i == 1:
                                print(f'ATK (When facing {str(i)} enemy):')
                            else:
                                print(f'ATK (When facing {str(i)} enemies):')
                                    
                            if flat:
                                activeCondATK = [atkPerBuff, atkFlatBuff + ((i-1)*int(buff))]
                                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + ((i-1)*int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, i)
                            else:
                                activeCondATK = [atkPerBuff + ((i-1)*int(buff)), atkFlatBuff]
                                calcATKCond(characterKit, copyCond, atkPerBuff + ((i-1)*int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, i)
                else:
                    for i in range(startLoop, limitLoop):
                        if i == 1:
                            print(f'ATK (When facing {str(i)} enemy):')
                        else:
                            print(f'ATK (When facing {str(i)} enemies):')
                                
                        if flat:
                            activeCondATK = [atkPerBuff, atkFlatBuff + ((i-1)*int(buff))]
                            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + ((i-1)*int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, i)
                        else:
                            activeCondATK = [atkPerBuff + ((i-1)*int(buff)), atkFlatBuff]
                            calcATKCond(characterKit, copyCond, atkPerBuff + ((i-1)*int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, i)
            else:
                if "limit" in locals():
                    limitLoop = int(limit/buff)+1
                for i in range(startLoop, limitLoop):
                    if i == 1:
                        print(f'ATK (When facing {str(i)} enemy):')
                    else:
                        print(f'ATK (When facing {str(i)} enemies):')
                        
                    if flat:
                        activeCondATK = [atkPerBuff, atkFlatBuff + (i*int(buff))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i*int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    else:
                        activeCondATK = [atkPerBuff + (i*int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i*int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("When facing only 1 enemy"):
            if enemyCount <= 1:
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, 1)   
                condition = condition.replace('hen facing', 'hen not facing')
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif (condition.__contains__("At the start of each turn")):
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1
            for i in range(1, limitLoop):
                activeCondATK = [atkPerBuff + (i*int(buff)), atkFlatBuff]
                print(f'ATK (Turn {str(i)}):')
                calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            if "limit" in locals():
                if limit % int(buff) != 0:
                    activeCondATK = [atkPerBuff + limit, atkFlatBuff]
                    print(f'ATK (Turn {str(i+1)}):')
                    calcATKCond(characterKit, copyCond, atkPerBuff + limit, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif (condition.__contains__("at the start of each turn")):
            # Test with TEQ HEP SSJ Vegeta, AGL WT Kid Gohan            
            condition = condition.replace('When HP is ', 'When HP is not ')
            print(f'ATK {condition.split(", ")[0]})')
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                
            condition = condition.replace('When HP is not', 'When HP is')
            condition = condition.replace(f", (up to {limit}%) at the start of each turn)", "")
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1
            for i in range(1, limitLoop):
                print(f'ATK {condition}, turn {str(i)}):')
                if flat:
                    activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                else:
                    activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                    calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif (condition.__contains__("For every turn passed")):
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1

            for i in range(0, limitLoop):
                activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                print(f'ATK ({str(i)} turns passed):')
                calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("The more HP remaining"):
            for i in range(0, 101):
                if i % 10 == 0:
                    print("ATK at " + str(i) + "% HP:")
                    if flat:
                        activeCondATK = [atkPerBuff, int(atkFlatBuff + (int(buff)*(i/100)))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, int(atkFlatBuff + (int(buff)*(i/100))), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    else:
                        activeCondATK = [int(atkPerBuff + (int(buff)*(i/100))), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, int(atkPerBuff + (int(buff)*(i/100))), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        elif condition.__contains__("The less HP remaining"):
            for i in range(0, 101):
                if i % 10 == 0:
                    print("ATK at " + str(i) + "% HP:")
                    if flat:
                        activeCondATK = [atkPerBuff, int(atkFlatBuff + (int(buff) - (int(buff)*(i/100))))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, int(atkFlatBuff + (int(buff) - (int(buff)*(i/100)))), linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                    else:
                        activeCondATK = [int(atkPerBuff + (int(buff) - (int(buff)*(i/100)))), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, int(atkPerBuff + (int(buff) - (int(buff)*(i/100)))), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
        else:
            if condition.__contains__('self excluded'):
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
            else:
                activeCondATK = [newPerBuff, newFlatBuff]
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
                
                condition = condition.replace(' is ', ' is not ')
                condition = condition.replace('As ', 'Not as ')
                condition = condition.replace('When facing ', 'When not facing ')
                condition = condition.replace(' are ', ' are not ')
                condition = condition.replace(' are not no', ' are')
                condition = condition.replace(" has", " doesn't have")
                condition = condition.replace(", as the ", ", not as the ")
                condition = condition.replace("(For ", "(After ")
                condition = condition.replace("once only", "after one-time buff")
                condition = condition.replace('great chance', 'without RNG chance')
                condition = condition.replace('high chance', 'without RNG chance')
                
                if condition.__contains__('Activates the Entrance Animation'):
                    condition = "(Without Entrance buff)"
                
                activeCondATK = [atkPerBuff, atkFlatBuff]
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, kiObtained, enemyCount)
    else:
        print(f'{characterKit.atk_max} (Base ATK Stat)')
        # Duo 200% lead by default
        lead = 5
        # Dev note: Temp condition, manually checks for units supported under 220% leads:
        # - Vegto, Gogta, SSBE, Monke, Rice, Frank, Ultra Vegeta 1, Fishku, Cell Games,
        # U7 Pawn, U6 Pawn, KFC, Serious Tao
        if ((("Earth-Protecting Heroes" in characterKit.categories or 
        "Fused Fighters" in characterKit.categories or
        "Pure Saiyans" in characterKit.categories) and
        ("Earth-Bred Fighters" in characterKit.categories or
        "Potara" in characterKit.categories)) or 
        (("Successors" in characterKit.categories or 
        "Fused Fighters" in characterKit.categories or
        "Pure Saiyans" in characterKit.categories) and
        ("Gifted Warriors" in characterKit.categories or
        "Fusion" in characterKit.categories)) or 
        (("Transformation Boost" in characterKit.categories or 
        "Gifted Warriors" in characterKit.categories) and
        ("Power Beyond Super Saiyan" in characterKit.categories)) or
        (("DB Saga" in characterKit.categories or 
        "Earth-Bred Fighters" in characterKit.categories) and
        ("Youth" in characterKit.categories) or
        ("Dragon Ball Seekers" in characterKit.categories)) or 
        (("Tournament Participants" in characterKit.categories or 
        "Worldwide Chaos" in characterKit.categories) and
        ("Androids" in characterKit.categories) or
        ("Accelerated Battle" in characterKit.categories)) or
        (("Representatives of Universe 7" in characterKit.categories or 
        "Full Power" in characterKit.categories) and
        ("Tournament Participants" in characterKit.categories) or
        ("Super Heroes" in characterKit.categories)) or
        (("Universe 6" in characterKit.categories or 
        "Rapid Growth" in characterKit.categories or 
        "Accelerated Battle" in characterKit.categories) and
        ("Tournament Participants" in characterKit.categories) or
        ("Super Bosses" in characterKit.categories)) or
        (("Mission Execution" in characterKit.categories or 
        "Earth-Bred Fighters" in characterKit.categories) and
        ("Dragon Ball Seekers" in characterKit.categories) or
        ("Earthlings" in characterKit.categories)) or
        "Universe Survival Saga" in characterKit.categories or 
        "Giant Ape Power" in characterKit.categories or
        "Full Power" in characterKit.categories or 
        "Battle of Fate" in characterKit.categories or
        "Universe 6" in characterKit.categories):
            lead = 5.4
        ATK = int(characterKit.atk_max*lead) # Apply leader skill
        print(f'{ATK} (With Duo {int(((lead-1)*100)/2)}% Leader Skill)')
        activeATK = int(ATK * (1 + (activeCondATK[0]/100)))
        ATK = int(ATK * (1 + (atkPerBuff/100))) # Apply SoT percentage buffs
        print(f'{ATK} (With {atkPerBuff}% Passive Buff)')
        activeATK = int(activeATK + activeCondATK[1])
        ATK = int(ATK + atkFlatBuff) # Apply SoT flat buffs
        print(f'{ATK} (With {atkFlatBuff} Flat Passive Buff)')
        activeATK = int(activeATK + (activeATK * (linkBuffs/100)))
        ATK = int(ATK + (ATK * (linkBuffs/100))) # Apply link buffs
        print(f'{ATK} (With {linkBuffs}% Link Skill Buff)')
        
        if characterKit.dokkan_fields:
            domainBuff = 0
            for line in characterKit.dokkan_fields[1].split(';'):
                if line.__contains__(" allies' ATK "):
                    buff = line.split('+')[1]
                    buff = int(buff.split('%')[0])
                    if characterKit.element1 in line:
                        domainBuff += buff
                        if line.__contains__(', plus an additional ATK'):
                            line = line.split(', ')[1]
                            buff = line.split('+')[1]
                            buff = int(buff.split('%')[0])
                            for category in characterKit.categories:
                                if category in line:
                                    domainBuff += buff
                                    break
                            if characterKit.unitClass in line:
                                domainBuff += buff
                            break
                        break
                    for category in characterKit.categories:
                        if category in line:
                            domainBuff += buff
                            break
                    
            ATK = int(ATK + (ATK * (domainBuff/100))) # Apply domain skill buffs
            print(f'{ATK} (With {domainBuff}% Domain Skill Buff: {characterKit.dokkan_fields[0]})')
            calcActiveATK(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional)
            print(f'{ATK} (Without Domain Skill Buff)')
        
        calcActiveATK(characterKit, ATK, activeATK, onAttackATK, crit, superEffective, additional)

def calculateStat(condition, line, statPerBuff, statFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, categories):   
    print(f'{condition} - {line}')
    if (condition.__contains__('The more HP remaining') or
    condition.__contains__('The less HP remaining')):
        buff = line.split('(up to ')[1]
        buff = buff.split(')')[0]
    else:
        buff = line.split(' +')[1]
    buff = buff.replace(" and launches an additional attack", "")
    
    flat = True
    if buff.split(' ')[0].__contains__('%'):
        flat = False
        if buff.split('%')[1] != ' ' and buff.split('%')[1] != '':
            if not '%'.join(buff.split('%')[1:]).__contains__(' for characters who also belong'):
                condition += ',' + '%'.join(buff.split('%')[1:])
        buff = buff.split('%')[0]
    else:
        if len(buff.split(' ')) > 2:
            condition += ', ' + ' '.join(buff.split(' ')[1:])
    
    condition = condition.replace(', and DEF', '')
    buff = buff.replace(' and DEF', '')
    if condition == 'Basic effect(s)':
        if flat:
            statFlatBuff += int(buff)
        else:
            statPerBuff += int(buff)
    elif (condition.__contains__("When attacking") or
    condition.__contains__("when attacking") or
    condition.__contains__("final blow") or
    condition.__contains__("receiving an attack") or
    condition.__contains__("After receiving") or
    condition.__contains__("evading an attack") or
    condition.__contains__("After guard is activated") or
    condition.__contains__("henever guard is activated") or
    condition.__contains__("For every attack evaded") or
    condition.__contains__("or every attack performed") or
    condition.__contains__("For every Super Attack performed") or
    condition.__contains__("For every attack received") or
    (condition.__contains__("After performing ") and condition.__contains__("ttack(s) in battle")) or
    (condition.__contains__("After performing ") and condition.__contains__("ttacks in battle")) or
    (condition.__contains__("After receiving ") and condition.__contains__("ttacks in battle")) or
    (condition.__contains__("After evading ") and condition.__contains__("ttacks in battle")) or
    condition.__contains__('Every time the character performs ') or
    condition.__contains__("After performing a Super Attack") or
    condition.__contains__("When the target enemy is in the following status: ")):
        if flat:
            print(f"ATK +{buff} ({condition})")
            onAttackATK.insertLine(f"ATK +{buff} ({condition})")
            #onAttackStat[condition][0] = buff
        else:
            if line.__contains__('HP remaining, the greater the ATK boost'):
                buff = buff.split('up to ')[1]
                onAttackATK.insertLine(f"ATK +{buff}% ({condition}, the more HP remaining)")
            else:
                onAttackATK.insertLine(f"ATK +{buff}% ({condition})")
                #onAttackStat[condition][0] = buff
                #onAttackStat[condition][2] = '%'
    elif line.__contains__('hen attacking'):
        condition += ', when attacking'
        if flat:
            onAttackATK.insertLine(f"ATK +{buff} ({condition})")
        else:
            onAttackATK.insertLine(f"ATK +{buff}% ({condition})")
    else:
        if condSoTATK.searchLine(condition) != None:
            condSoTATK.replaceLine(condition, buff)
            #condSoTStat[condition][0] += buff
        else:
            if flat:
                condSoTATK.insertLine(f"ATK +{buff} ({condition})")
                #condSoTStat[condition][0] = buff
            else:
                condSoTATK.insertLine(f"ATK +{buff}% ({condition})")
                #condSoTStat[condition][0] = buff
                #condSoTStat[condition][2] = '%'
    return statPerBuff, statFlatBuff

# Read through kit, sepearate lines based on activiation condition (SoT vs. 'on attack')
# Then, calculate SoT attack and conditional SoT attack  
def calculateMain(characterKit, atkLinkBuffs, defLinkBuffs, crit):
    condSoTATK = LinkedList()
    condSoTDEF = LinkedList()
    onAttackATK = LinkedList()
    onAttackDEF = LinkedList()
    
    condSoTStat = dict()
    onAttackStat = dict()

    atkPerBuff = 0
    defPerBuff = 0
    atkFlatBuff = 0
    defFlatBuff = 0
    condition = ""
    flat = False
    additional = 0
    superEffective = False
    
    # Formats passive buff indicators (+/- instead of {passiveImg:up_g/down_r})
    if characterKit.passive_skill_itemized_desc:
        passive_skill = characterKit.passive_skill_itemized_desc.split()
        passive_skill = [word if not word.__contains__("{passiveImg:up_g}") else ("+" + word) for word in passive_skill]
        passive_skill = [word if not word.__contains__("{passiveImg:down_r}") else ("+-" + word) for word in passive_skill]
        passive_skill = [word if not word.__contains__("{passiveImg:once}") else ("(Once only) " + word) for word in passive_skill]
        characterKit.passive_skill_itemized_desc = ' '.join(passive_skill)
        characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('\n', ' ')
        characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('- ', '\n- ')
        characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace(' *', '\n*')
        
    characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('{passiveImg:up_g}', '')
    characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('{passiveImg:down_r}', '')
    characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('{passiveImg:once}', '')
    characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('{passiveImg:forever}', '')
    
    if characterKit.rarity == "UR" or characterKit.rarity == "LR":
        additional += 1
    
    if (characterKit.passive_skill_itemized_desc).__contains__('critical hit'):
        crit = True
    elif (characterKit.passive_skill_itemized_desc).__contains__('Attacks are effective against all Types'):
        superEffective = True
    
    for line in (characterKit.passive_skill_itemized_desc).splitlines():
        # Skips line if there is no character buff (debuff line, support passive no applicable, etc.)
        if (line.__contains__('{passiveImg:down_y}') or
        (line.__contains__('Type allies') and not line.__contains__(characterKit.element2)) or
        (line.__contains__('Class allies') and not line.__contains__(characterKit.element1)) or
        (line.__contains__("for allies whose names include ") and characterKit.name not in line)):
            continue
        
        if line.__contains__("*"):
            condition = line[1:-2]
        
        if ((line.__contains__(' and if there is ') or line.__contains__(' and per ')) and
        line.__contains__(', plus an additional ')):
            line = line.split(' and ')
            for linePart in line:
                if linePart.__contains__('ATK & DEF ') or linePart.__contains__('ATK, DEF '):
                    if linePart.__contains__('if there is '):
                        condition = condition + ', ' + linePart.split(', plus an additional ')[0]
                        linePart = '- ' + linePart.split(', plus an additional ')[1]
                    line = 'ATK ' + line.split('ATK ')[1]
                    atkPerBuff, atkFlatBuff = calculateStat(condition, linePart, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
                    defPerBuff, defFlatBuff = calculateStat(condition, linePart, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
                elif linePart.__contains__('ATK ') and linePart.__contains__('and DEF '):
                    line = 'ATK ' + line.split('ATK ')[1]
                    atkPerBuff, atkFlatBuff = calculateStat(condition, linePart, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
                    line = 'DEF ' + line.split(' and DEF ')[1]
                    defPerBuff, defFlatBuff = calculateStat(condition, linePart, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
                elif linePart.__contains__('ATK '):
                    linePart = 'ATK ' + linePart.split('ATK ')[1]
                    atkPerBuff, atkFlatBuff = calculateStat(condition, linePart, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
                elif linePart.__contains__('DEF '):
                    linePart = 'ATK ' + linePart.split('DEF ')[1]
                    defPerBuff, defFlatBuff = calculateStat(condition, linePart, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
            continue
        elif (line.__contains__(', plus an additional ') or
        line.__contains__(', plus an additional ')):
            line = line.split(', ')
            for linePart in line:
                if linePart.__contains__('ATK & DEF') or linePart.__contains__('ATK, DEF'):
                    linePart = 'ATK ' + linePart.split('ATK ')[1]
                    atkPerBuff, atkFlatBuff = calculateStat(condition, linePart, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
                    defPerBuff, defFlatBuff = calculateStat(condition, linePart, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
                elif linePart.__contains__('ATK ') and linePart.__contains__('and DEF'):
                    linePart = 'ATK ' + linePart.split('ATK ')[1]
                    atkPerBuff, atkFlatBuff = calculateStat(condition, linePart, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
                    linePart = 'DEF ' + linePart.split(' and DEF ')[1]
                    defPerBuff, defFlatBuff = calculateStat(condition, linePart, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
                elif linePart.__contains__('ATK '):
                    linePart = 'ATK ' + linePart.split('ATK ')[1]
                    atkPerBuff, atkFlatBuff = calculateStat(condition, linePart, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
                elif linePart.__contains__('DEF '):
                    linePart = 'DEF ' + linePart.split('DEF ')[1]
                    defPerBuff, defFlatBuff = calculateStat(condition, linePart, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
            continue
        
        line = line.replace('& chance of performing a critical hit ', '')
        if line.__contains__('} and chance of performing a critical hit '):
            line = line.replace(line[line.find('} and chance of performing'):], '}')
        elif (line.__contains__(') and chance of performing a critical hit ') and
        line.__contains__(') at')):
            line = line.split(') and')[0] + ') at' + line.split(') at')[1]
        elif line.__contains__(') and chance of performing a critical hit '):
            line = line.split(') and')[0] + ') within' + line.split(') within')[1]
        elif (line.__contains__('chance of performing a critical hit ') and
        line.__contains__('} and ATK ')):
            line = line.replace(line[line.find('chance of performing '):line.find('} and ')+6], '')
        elif line.__contains__('chance of performing a critical hit '):
            line = line.replace(line[line.find(' and '):line.find(' critical hit ')+13], '')
        if (line.__contains__("} and ") and
        line.__contains__("chance of evading enemy's attack ")):
            line = line.replace(line[line.find('} and '):line.find('attack ')+6], '}')
            
        if (((line.__contains__("aunches an additional attack that has a") or
        line.__contains__("chance of launching an additional attack that has a")) and
        line.__contains__("chance of becoming a Super Attack")) or 
        line.__contains__("aunches an additional Super Attack") or 
        line.__contains__("launching an additional Super Attack")):
            additional += 1
        elif (line.__contains__("aunches ") and
        line.__contains__(" additional attacks, each of which has a") and
        line.__contains__("chance of becoming a Super Attack")):
            additional += int((line.split('aunches ')[1]).split(' additional attacks')[0])
            
        if ((line.__contains__("Counters with ") or
             line.__contains__("counters with ") or
             line.__contains__("countering with ")) and
            line.__contains__(" power")):
            onAttackATK.insertLine(line + " (" + condition + ")")
        
        if (line.__contains__('(Once only)') and 
        (line.__contains__('ATK') or line.__contains__('DEF'))):
            condition += ', once only'
        
        if (condition.__contains__("When the Finish Effect is activated") and
        line.__contains__('ATK +')):
            characterKit.finish_skills.append(line)
            continue
        
        if line.__contains__('ATK & DEF') or line.__contains__('ATK, DEF'):
            if line.__contains__(' chance of '):
                line += line.split(' ')[1].lower() + ' chance'
            
            line = 'ATK ' + line.split('ATK ')[1]
            atkPerBuff, atkFlatBuff = calculateStat(condition, line, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
            defPerBuff, defFlatBuff = calculateStat(condition, line, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
        elif line.__contains__('ATK ') and line.__contains__('and DEF'):
            if line.__contains__(' chance of '):
                line += line.split(' ')[1].lower() + ' chance'
            
            line = 'ATK ' + line.split('ATK ')[1]
            atkPerBuff, atkFlatBuff = calculateStat(condition, line, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
            line = 'DEF ' + line.split(' and DEF ')[1]
            defPerBuff, defFlatBuff = calculateStat(condition, line, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)
        elif line.__contains__('ATK '):
            if line.__contains__(' chance of '):
                line += line.split(' ')[1].lower() + ' chance'
            
            line = 'ATK ' + line.split('ATK ')[1]
            atkPerBuff, atkFlatBuff = calculateStat(condition, line, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
        elif line.__contains__('DEF '):
            if line.__contains__(' chance of '):
                line += ' ' + line.split(' ')[1].lower() + ' chance'
            
            line = 'DEF ' + line.split('DEF ')[1]
            defPerBuff, defFlatBuff = calculateStat(condition, line, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)

    activeCondATK = [atkPerBuff, atkFlatBuff]
    #print(condSoTStat)
    #print(onAttackStat)
    print(f"\nInitial percent buffs: {atkPerBuff}% ATK, {defPerBuff}% DEF")
    print(f"Initial flat buffs: {atkFlatBuff} ATK, {defFlatBuff} DEF\n")
    
    calcATKCond(characterKit, condSoTATK, atkPerBuff, atkFlatBuff, atkLinkBuffs, onAttackATK, crit, superEffective, additional, activeCondATK, 0, 0)
    #input("Click any button to continue with unit defense:")
    #os.system('cls')
    #calcDEFCond(characterKit, condSoTDEF, defLinkBuffs, onAttackDEF, crit, superEffective, additional, 1)
    
# Read through kit, sepearate lines based on activiation condition (SoT vs. 'on attack')
# Then, calculate SoT defense and conditional SoT defense  
def calculateLinks(characterKit, partnerKit):
    os.system('cls')
    print(f"Calculating: {characterKit.element2} {characterKit.rarity} {characterKit.name} (Linked with {partnerKit.element2} {partnerKit.rarity} {partnerKit.name}):")
    
    # Find all shared links
    sharedLinks = []
    if (characterKit.name != partnerKit.name or
    (int(partnerKit.id) >= 4000000 and characterKit.id != partnerKit.id)):
        print("\nShared Links:")
        for sharedLink in characterKit.card_links:
            if sharedLink in partnerKit.card_links:
                print(f"- {sharedLink[0]} - {sharedLink[1]}")
                sharedLinks.append(sharedLink[1])
    else:
        print("Unit cannot link with partner (Shared name)")
        calculateMain(characterKit, 0, 0, False)
        return

    if not sharedLinks:
        print("Unit cannot link with partner (No shared links)")
        calculateMain(characterKit, 0, 0, False)
        return
    else:
        # Calculate shared link buffs
        kiLinkBuffs = 0
        atkLinkBuffs = 0
        defLinkBuffs = 0
        critLinkBuffs = 0
        evadeLinkBuffs = 0
        damageReduceLinkBuffs = 0
        recoveryLinkBuffs = 0
        defLinkDebuffs = 0
        crit = False
    
        for linkStats in sharedLinks:
            if linkStats.__contains__("Ki +"):
                kiBuff = linkStats[linkStats.find('Ki +')+4:]
                if kiBuff.__contains__(' '):
                    kiBuff = kiBuff[:kiBuff.find(' ')]
                if kiBuff.__contains__(';'):
                    kiBuff = kiBuff[:kiBuff.find(';')]
                if kiBuff.__contains__(','):
                    kiBuff = kiBuff[:kiBuff.find(',')]
                kiLinkBuffs += int(kiBuff)
            if (linkStats.__contains__("ATK +") or
            linkStats.__contains__("ATK & ") or
            linkStats.__contains__("ATK, DEF &")):
                atkBuff = linkStats[linkStats.find('ATK ')+4:]
                if linkStats.__contains__("plus an additional ATK +"):
                    atkBuff2 = atkBuff[atkBuff.find('ATK +')+5:]
                    atkBuff2 = atkBuff2[:atkBuff2.find('%')]
                    atkLinkBuffs += int(atkBuff2)
                atkBuff = atkBuff[atkBuff.find('+')+1:]
                atkBuff = atkBuff[:atkBuff.find('%')]
                atkLinkBuffs += int(atkBuff)
            if linkStats.__contains__("DEF +"):
                defBuff = linkStats[linkStats.find('DEF +')+5:]
                defBuff = defBuff[:defBuff.find('%')]
                defLinkBuffs += int(defBuff)
            if linkStats.__contains__("chance of performing a critical hit +"):
                crit = True
                critBuff = linkStats[linkStats.find('chance of performing a critical hit +')+37:]
                critBuff = critBuff[:critBuff.find('%')]
                critLinkBuffs += int(critBuff)
            if linkStats.__contains__("chance of evading enemy's attack"):
                evadeBuff = linkStats[linkStats.find('chance of evading enemy')+59:]
                evadeBuff = evadeBuff[:evadeBuff.find('%')]
                evadeLinkBuffs += int(evadeBuff)
            if linkStats.__contains__("reduces damage received by "):
                damageReduceBuff = linkStats[linkStats.find('reduces damage received by ')+27:]
                damageReduceBuff = damageReduceBuff[:damageReduceBuff.find('%')]
                damageReduceLinkBuffs += int(damageReduceBuff)
            if linkStats.__contains__("ecovers "):
                recoveryBuff = linkStats[linkStats.find('ecovers ')+8:]
                recoveryBuff = recoveryBuff[:recoveryBuff.find('% HP')]
                recoveryLinkBuffs += int(recoveryBuff)
            if linkStats.__contains__("enemies' DEF -"):
                defDebuff = linkStats[linkStats.find('DEF -')+5:]
                defDebuff = defDebuff[:defDebuff.find('%')]
                defLinkDebuffs += int(defDebuff)
        print(f"\nTotal Link Buffs:")
        print(f"- Ki +{str(kiLinkBuffs)}, ATK +{str(atkLinkBuffs)}%, DEF +{str(defLinkBuffs)}%")
        print(f"- Chance of performing a critical hit +{str(critLinkBuffs)}%")
        print(f"- Chance of evading enemy's attack +{evadeLinkBuffs}%")
        print(f"- Damage reduction rate +{damageReduceLinkBuffs}%")
        print(f"- Recovers {recoveryLinkBuffs}% HP")
        print(f"- All enemies' DEF -{defLinkDebuffs}%")
        
        calculateMain(characterKit, atkLinkBuffs, defLinkBuffs, crit)
   
def formatSpecial(special):
    if (not special.__contains__('Causes') and not
    special.__contains__('causes')):
        special = 'Causes ' + special[0].lower() + special[1:]
    if (not special.__contains__('damage to enemy') and not
    special.__contains__('stunning the enemy')):
        special = special.replace('damage', 'damage to enemy')
    
    if special.__contains__('Raises DEF and') or special.__contains__('Raises DEF,'):
        special = special.replace('Raises DEF', 'Raises DEF by 30%')
    elif special.__contains__('Greatly raises DEF and') or special.__contains__('Greatly raises DEF,'):
        special = special.replace('Raises DEF', 'Raises DEF by 50%')
    
    if special.__contains__('Raises ATK & DEF'):
        special = special.replace('Raises ATK & DEF', 'Raises ATK & DEF by 30%')
    elif special.__contains__('raises ATK for ') and special.__contains__(' turns'):
        special = special.replace('raises ATK', 'raises ATK by 50%')
    elif special.__contains__('raises ATK for ') and special.__contains__(' turn'):
        special = special.replace('raises ATK', 'raises ATK by 30%')
    elif special.__contains__('Raises ATK'):
        special = special.replace('Raises ATK', 'Raises ATK by 30%')
    elif special.__contains__('Greatly raises ATK & DEF'):
        special = special.replace('Greatly raises ATK & DEF', 'Raises ATK & DEF by 50%')
    elif special.__contains__('Greatly raises ATK'):
        special = special.replace('Greatly raises ATK', 'Raises ATK by 50%')
    elif special.__contains__('greatly raises ATK'):
        special = special.replace('greatly raises ATK', 'raises ATK by 50%')
    elif special.__contains__('Massively raises ATK & DEF '):
        special = special.replace('Massively raises ATK & DEF', 'Raises ATK & DEF by 100%')
    elif special.__contains__('Massively raises ATK'):
        special = special.replace('Massively raises ATK', 'Raises ATK by 100%')
        
    if special.__contains__(", \nallies'"):
        special = special.replace(', \nallies', ';\nraises allies')
    if special.__contains__(' and \nraises allies'):
        special = special.replace(' and \nraises', '; \nraises')
    if special.__contains__('enemy \nand '):
        special = special.replace('enemy \nand ', 'enemy; \nraises ')
        special = special.replace('raises raises', 'raises')
    if special.__contains__("ATK +"):
        special = special.replace('ATK +', 'ATK by ')
    return special
   
# Helper method to get all unit details
def getPartnerKit(partnerID):
    if partnerID % 2 == 0:
        partnerID += 1
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
        },
    )
    url = f'https://dokkan.wiki/api/cards/{partnerID}'
    
    # Send a GET request to fetch the webpage content (Returns None if page fails)
    partnerKit = Partner(partnerID, '', '', 0, [])
    if (scraper.get(url).status_code) == 200:
        response = scraper.get(url).json()
        for item1, item2 in response.items():
            id: int
            name: str
            rarity: str
            element: int
            card_links: list
            match item1:
                case 'card':
                    partnerKit.name = item2['name']
                    match item2['rarity']:
                        case 0:
                            partnerKit.rarity = 'N'
                        case 1:
                            partnerKit.rarity = 'R'
                        case 2:
                            partnerKit.rarity = 'SR'
                        case 3:
                            partnerKit.rarity = 'SSR'
                        case 4:
                            partnerKit.rarity = 'UR'
                        case 5:
                            partnerKit.rarity = 'LR'
                            
                    match item2['element']:
                        case 0:
                            partnerKit.element2 = 'AGL'
                        case 1:
                            partnerKit.element2 = 'TEQ'
                        case 2:
                            partnerKit.element2 = 'INT'
                        case 3:
                            partnerKit.element2 = 'STR'
                        case 4:
                            partnerKit.element2 = 'PHY'
                        case 10:
                            partnerKit.element2 = 'AGL'
                        case 11:
                            partnerKit.element2 = 'TEQ'
                        case 12:
                            partnerKit.element2 = 'INT'
                        case 13:
                            partnerKit.element2 = 'STR'
                        case 14:
                            partnerKit.element2 = 'PHY'
                        case 20:
                            partnerKit.element2 = 'AGL'
                        case 21:
                            partnerKit.element2 = 'TEQ'
                        case 22:
                            partnerKit.element2 = 'INT'
                        case 23:
                            partnerKit.element2 = 'STR'
                        case 24:
                            partnerKit.element2 = 'PHY'
                case "card_links":
                    for link in item2:
                        partnerKit.card_links.append([link['name'],
                            link['level10_description']])
                        
        if partnerID >= 4000000:
            partnerKit.name += (' (<->)')
            
        os.system('cls')
        return partnerKit
    else:
        print('Failed to retrieve character information.')
        return None
    
# Helper method to get all unit details
def getKit(characterID):       
    if characterID % 2 == 0:
        characterID += 1
        
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
        },
    )
    url = f'https://dokkan.wiki/api/cards/{characterID}'
    # Send a GET request to fetch the webpage content (Returns None if page fails)
    characterKit = Unit(characterID, '', '', 0, 0, 0, '', '', 0, 0, 0, 0, '', '', '', '', '', '',
    '', [], [0, 0, 0], [], [], [], [], [], [], [], [])
    if (scraper.get(url).status_code) == 200:
        response = scraper.get(url).json()
        for item1, item2 in response.items():
            match item1:
                case 'card':
                    characterKit.name = item2['name']
                    match item2['rarity']:
                        case 0:
                            characterKit.rarity = 'N'
                        case 1:
                            characterKit.rarity = 'R'
                        case 2:
                            characterKit.rarity = 'SR'
                        case 3:
                            characterKit.rarity = 'SSR'
                        case 4:
                            characterKit.rarity = 'UR'
                        case 5:
                            characterKit.rarity = 'LR'

                    characterKit.hp_max = item2['hp_max']
                    characterKit.atk_max = item2['atk_max']
                    characterKit.def_max = item2['def_max']
                    match item2['element']:
                        case 0:
                            characterKit.element2 = 'AGL'
                        case 1:
                            characterKit.element2 = 'TEQ'
                        case 2:
                            characterKit.element2 = 'INT'
                        case 3:
                            characterKit.element2 = 'STR'
                        case 4:
                            characterKit.element2 = 'PHY'
                        case 10:
                            characterKit.element1 = 'Super'
                            characterKit.element2 = 'AGL'
                        case 11:
                            characterKit.element1 = 'Super'
                            characterKit.element2 = 'TEQ'
                        case 12:
                            characterKit.element1 = 'Super'
                            characterKit.element2 = 'INT'
                        case 13:
                            characterKit.element1 = 'Super'
                            characterKit.element2 = 'STR'
                        case 14:
                            characterKit.element1 = 'Super'
                            characterKit.element2 = 'PHY'
                        case 20:
                            characterKit.element1 = 'Extreme'
                            characterKit.element2 = 'AGL'
                        case 21:
                            characterKit.element1 = 'Extreme'
                            characterKit.element2 = 'TEQ'
                        case 22:
                            characterKit.element1 = 'Extreme'
                            characterKit.element2 = 'INT'
                        case 23:
                            characterKit.element1 = 'Extreme'
                            characterKit.element2 = 'STR'
                        case 24:
                            characterKit.element1 = 'Extreme'
                            characterKit.element2 = 'PHY'
                        
                    characterKit.eball_mod_mid = item2['eball_mod_mid']
                    characterKit.eball_mod_mid_num = item2['eball_mod_mid_num']
                    characterKit.eball_mod_max = item2['eball_mod_max']
                    characterKit.eball_mod_max_num = item2['eball_mod_max_num']
                    characterKit.title = item2['title']
                    characterKit.leader_skill = item2['leader_skill']

                    if 'passive_skill_name' in item2:
                        characterKit.passive_skill_name = item2['passive_skill_name']
                        characterKit.passive_skill_itemized_desc = item2['passive_skill_itemized_desc']
                            
                    if 'active_skill_name' in item2:
                        characterKit.active_skill_name = item2['active_skill_name']
                        characterKit.active_skill_effect = item2['active_skill_effect']
                        characterKit.active_skill_condition = item2['active_skill_condition']
                case "categories":
                    if item2:
                        for category in item2:
                            characterKit.categories.append(category['name'])
                case "potential":
                    print(f"0 - No Hidden Potential boost (0%)")
                    print(f"1 - {item2[0]} (55%)")
                    print(f"2 - {item2[1]} (69%)")
                    print(f"3 - {item2[2]} (79%)")
                    print(f"4 - {item2[3]} (90%)")
                    print(f"5 - {item2[4]} (100%)")
                    hipo = int(input("Select Hidden Potential boost of unit (0-5): "))
                    
                    match hipo:
                        case 1:
                            characterKit.potential = [0, 0, 0]
                        case 1:
                            characterKit.potential = [item2[0]['hp'], item2[0]['atk'], item2[0]['def']]
                        case 2:
                            characterKit.potential = [item2[1]['hp'], item2[1]['atk'], item2[1]['def']]
                        case 3:
                            characterKit.potential = [item2[2]['hp'], item2[2]['atk'], item2[2]['def']]
                        case 4:
                            characterKit.potential = [item2[3]['hp'], item2[3]['atk'], item2[3]['def']]
                        case 5:
                            characterKit.potential = [item2[4]['hp'], item2[4]['atk'], item2[4]['def']]
                case "specials":
                    if item2:
                        for special in item2:
                            if not special['name'] == "None":
                                special['description'] = formatSpecial(special['description'])
                                if 'special_bonus_2' in special:
                                    if special['special_bonus_2'].__contains__(' Super Attack when Ki '):
                                        ki = special['special_bonus_2'].split('when Ki is ')[1]
                                        ki = int(ki.split(' or more!')[0])
                                        special['eball_num_start'] = ki
                                        del special['special_bonus_2']
                                        characterKit.specials.append(tuple([special['name'],
                                        special['description'], special['eball_num_start'],
                                        special['special_bonus_1']]))
                                    elif special['special_bonus_1'].__contains__(' Super Attack when Ki '):
                                        ki = special['special_bonus_1'].split('when Ki is ')[1]
                                        ki = int(ki.split(' or more!')[0])
                                        special['eball_num_start'] = ki
                                        special['special_bonus_1'] = special['special_bonus_2']
                                        del special['special_bonus_2']
                                        characterKit.specials.append(tuple([special['name'],
                                        special['description'], special['eball_num_start'],
                                        special['special_bonus_1']]))
                                    else:
                                        characterKit.specials.append(tuple([special['name'],
                                        special['description'], special['eball_num_start'],
                                        special['special_bonus_1'], special['special_bonus_2']]))
                                elif 'special_bonus_1' in special:
                                    if special['special_bonus_1'].__contains__(' Super Attack when Ki '):
                                        ki = special['special_bonus_1'].split('when Ki is ')[1]
                                        ki = int(ki.split(' or more!')[0])
                                        special['eball_num_start'] = ki
                                        del special['special_bonus_1']
                                        characterKit.specials.append(tuple([special['name'],
                                        special['description'], special['eball_num_start']]))
                                    else:
                                        if 'causality_description' in special:
                                            characterKit.specials.append(tuple([special['name'],
                                        special['description'], special['eball_num_start'],
                                        special['special_bonus_1'], special['causality_description'].replace('\n', '')]))
                                        else:
                                            characterKit.specials.append(tuple([special['name'],
                                            special['description'], special['eball_num_start'],
                                            special['special_bonus_1']]))
                                else:
                                    characterKit.specials.append(tuple([special['name'],
                                    special['description'], special['eball_num_start']]))
                case "transformations":
                    for transformation in item2:
                        if (transformation['next_card_id'] != characterID and
                        transformation['next_card_id'] > characterID):
                            characterKit.transformations.append([transformation['next_card_id'],
                            transformation['next_card']['name']])
                case "optimal_awakening_growths":
                    EZA = 0
                    if any(d["step"] == 8 for d in item2) or any(d["step"] == 4 for d in item2):
                        EZA = int(input('Select option for EZA (0 - Base; 1 - EZA; 2 - SEZA): '))
                    elif any(d["step"] == 7 for d in item2) or any(d["step"] == 3 for d in item2):
                        EZA = int(input('Select option for EZA (0 - Base; 1 - EZA): '))
                            
                    for optimal_awakening_growth in item2:
                        if EZA != 0:
                            while not '(Extreme)' in characterKit.specials[0][0]:
                                characterKit.specials.pop(0)

                        if ((optimal_awakening_growth["step"] == 3 or
                        optimal_awakening_growth["step"] == 7) and EZA == 1):
                            characterKit.leader_skill = optimal_awakening_growth["leader_skill_description"]
                            characterKit.hp_max = optimal_awakening_growth["hp_max"]
                            characterKit.atk_max = optimal_awakening_growth["atk_max"]
                            characterKit.def_max = optimal_awakening_growth["def_max"]
                            characterKit.passive_skill_name = optimal_awakening_growth["passive_skill_name"]
                            characterKit.passive_skill_itemized_desc = optimal_awakening_growth["passive_skill_itemized_desc"]
                        elif ((optimal_awakening_growth["step"] == 4 or
                        optimal_awakening_growth["step"] == 8) and EZA == 2):
                            characterKit.leader_skill = optimal_awakening_growth["leader_skill_description"]
                            characterKit.hp_max = optimal_awakening_growth["hp_max"]
                            characterKit.atk_max = optimal_awakening_growth["atk_max"]
                            characterKit.def_max = optimal_awakening_growth["def_max"]
                            characterKit.passive_skill_name = optimal_awakening_growth["passive_skill_name"]
                            characterKit.passive_skill_itemized_desc = optimal_awakening_growth["passive_skill_itemized_desc"]
                        elif EZA == 0:
                            while '(Extreme)' in characterKit.specials[-1][0]:
                                characterKit.specials = characterKit.specials[:-1]
                case "card_links":
                    for link in item2:
                        characterKit.card_links.append([link['name'],
                            link['level10_description']])
                case "finish_skills":
                    for finish_skill in item2:
                        finish_skill['effect_description'] = finish_skill['effect_description'].replace('\n', '')
                        finish_skill['condition_description'] = finish_skill['condition_description'].replace('\n', '')
                        characterKit.finish_skills.append([finish_skill['name'],
                        finish_skill['effect_description'], finish_skill['condition_description']])
                case "standby_skills":
                    for standby_skill in item2:
                        characterKit.standby_skills = [standby_skill['name'],
                        standby_skill['effect_description'], standby_skill['condition_description']]
                        characterKit.standby_skills[1] = characterKit.standby_skills[1].replace('\n', '')
                        characterKit.standby_skills[2] = characterKit.standby_skills[2].replace('\n', '')
                case "dokkan_fields":
                    for dokkan_field in item2:
                        characterKit.dokkan_fields = [dokkan_field['name'],
                        dokkan_field['description']]
                        characterKit.dokkan_fields[1] = characterKit.dokkan_fields[1].replace('\n', '')
            
        characterKit.leader_skill = characterKit.leader_skill.replace('\n', '')
        characterKit.active_skill_effect = characterKit.active_skill_effect.replace('\n', '')
        characterKit.active_skill_condition = characterKit.active_skill_condition.replace('\n', '')
        
        # Optional selection for GBL/JP kits for:
        # Special: TEQ SSJ Goku, STR 'Bye Guys' SSJ Goku, INT Final Form Cooler
        # Otherworld: TEQ Angel King Cold, PHY Super Kaioken Goku, STR/INT Pikkon,
        # INT/STR Angel Goku, INT/STR SSJ Angel Goku
        # Dokkan Coin: PHY SSB Goku, AGL GT Goku, INT Goku, TEQ Kid Goku
        # Etc: INT Super Trunks
        if (characterID == 1004201 or
            characterID == 1003991 or characterID == 1002481 or
            characterID == 1010701 or characterID == 1010661 or
            characterID == 1010631 or characterID == 1011041 or
            characterID == 1010641 or characterID == 1010651 or
            characterID == 1008391 or characterID == 1008381 or
            characterID == 1008371 or characterID == 1008361):
            if input("Test JP Kit? (y/n): ") == 'y':
                match characterID:
                    case 1004201:
                        characterKit.rarity = 'SSR'
                        characterKit.hp_max = 6463
                        characterKit.atk_max = 5869
                        characterKit.def_max = 3299
                        characterKit.potential = [0, 0, 0]
                    case 1010641:
                        characterKit.element2 = 'STR'
                        print(characterKit.specials[0][1])
                        characterKit.specials.pop()
                        characterKit.specials.append(tuple([special['name'],
                        'Causes huge damage to enemy', special['eball_num_start'],
                        special['special_bonus_1']]))
                    case 1010651:
                        characterKit.element2 = 'STR'
            
                        match hipo:
                            case 1:
                                characterKit.potential = [1200, 1200, 1200]
                            case 2:
                                characterKit.potential = [2220, 2460, 1980]
                            case 3:
                                characterKit.potential = [2400, 2640, 2160]
                            case 4:
                                characterKit.potential = [2586, 3060, 2346]
                            case 5:
                                characterKit.potential = [3000, 3240, 2760]
                    case 1010631:
                        characterKit.element2 = 'INT'
                        characterKit.leader_skill = characterKit.leader_skill.replace('STR Type', 'INT Type')
                        characterKit.card_links[0] = ['Supreme Warrior', 'Ki +2 and ATK +10%']
            
                        match hipo:
                            case 2:
                                characterKit.potential = [3700, 3700, 3700]
                            case 3:
                                characterKit.potential = [4000, 4000, 4000]
                            case 4:
                                characterKit.potential = [4310, 4700, 4310]
                            case 5:
                                characterKit.potential = [5000, 5000, 5000]
                    case 1011041:
                        characterKit.element2 = 'INT'
                        characterKit.leader_skill = characterKit.leader_skill.replace('STR Type', 'INT Type')
                        characterKit.card_links[4] = ['Supreme Warrior', 'Ki +2 and ATK +10%']
                        characterKit.card_links[6] = ['Shattering the Limit', 'Ki +2 and ATK & DEF +5%']
                
                        match hipo:
                            case 2:
                                characterKit.potential = [3700, 3700, 3700]
                            case 3:
                                characterKit.potential = [4000, 4000, 4000]
                            case 4:
                                characterKit.potential = [4310, 4700, 4310]
                            case 5:
                                characterKit.potential = [5000, 5000, 5000]
                    case 1010661:
                        characterKit.card_links[6] = ['Shattering the Limit', 'Ki +2 and ATK & DEF +5%']
                    case 1003991:
                        characterKit.rarity = 'SSR'
                        characterKit.specials = [tuple([characterKit.specials[0][0], characterKit.specials[0][1], characterKit.specials[0][2]])]
                        characterKit.hp_max = 5875
                        characterKit.atk_max = 5050
                        characterKit.def_max = 3188
                        characterKit.potential = [0, 0, 0]
                    case 1010701:
                        characterKit.specials = [tuple([characterKit.specials[0][0], "Causes supreme damage to enemy \nand lowers DEF", characterKit.specials[0][2]])]
                    case 1002481:
                        characterKit.card_links[2] = ['Cold Judgement', 'DEF +25%']
                    case 1008391:
                        characterKit.specials = [tuple([special['name'],
                        special['description'], special['eball_num_start']])]
                    case 1008381:
                        characterKit.specials = [tuple([special['name'],
                        special['description'], special['eball_num_start']])]
                    case 1008371:
                        characterKit.specials = [tuple([special['name'],
                        special['description'], special['eball_num_start']])]
                    case 1008361:
                        characterKit.specials = [tuple([special['name'],
                        special['description'], special['eball_num_start']])]
        # Optional selection for GBL/JP kits for INT Kid Goku
        elif (characterID == 1016571):
            if input("Test JP Kit? (y/n): ") != 'y':
                characterKit.active_skill_effect = "Massively raises ATK temporarily and causes ultimate damage to enemy"
        # Clean up for F2P UR TEQ Kid Goku and UR STR Arale (Not properly translated on GBL)
        elif characterID == 1010611 or characterID == 1010621:
            match characterID:
                    case 1010611:
                        characterKit.title = "Kiiin! Charge"
                        characterKit.name = "Goku (Youth)"
                        characterKit.leader_skill = "STR Type HP +77%"
                        characterKit.passive_skill_name = "Energetic Assault"
                    case 1010621:
                        characterKit.title = "Quick Trip on the Magic Cloud"
                        characterKit.name = "Arale Norimaki"
                        characterKit.leader_skill = "TEQ Type HP +77%"
                        characterKit.passive_skill_name = "Child's Ride: Flying Nimbus"
        characterKit.hp_max += characterKit.potential[0]
        characterKit.atk_max += characterKit.potential[1]
        characterKit.def_max += characterKit.potential[2]
        
        # Dev Note: Why do WT Goten and Trunks have different wordings for the same passive?
        if characterID == 1024221:
            characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('- ATK & DEF +20% and if there is another "Bond of Friendship" Category ally attacking in the same turn, plus an additional ATK & DEF +5%', '- ATK & DEF +20%\n- An additional ATK & DEF +5% when there is another "Bond of Friendship" Category ally attacking in the same turn')
        elif characterID == 1031051:
            characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('ATK100%', 'ATK 100%') # In-game parsing error for SSR SSJ3 Daima Vegeta
        elif characterID == 1013261:
            characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('- ATK & DEF 12%{passiveImg:up_g} and per "Giant Form" Category ally on the team, plus an additional ATK & DEF 1%{passiveImg:up_g} (up to 3%)', '- ATK & DEF 12%{passiveImg:up_g}\n- An additional ATK & DEF 1%{passiveImg:up_g} per "Giant Form" Category ally on the team (up to 3%)')
        elif characterID == 1013121:
            characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace("- ATK & DEF 5%{passiveImg:down_y}", "- All enemies' ATK & DEF 5%{passiveImg:down_y}")
        elif (characterID == 1015891 or characterID == 1015901) and EZA == 0:
            passive1 = characterKit.passive_skill_itemized_desc[characterKit.passive_skill_itemized_desc.find(' and if there is a '):characterKit.passive_skill_itemized_desc.find('n additional')]
            characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace(passive1, '\n- A')
            characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('3%{passiveImg:up_g}', '3%{passiveImg:up_g}' + passive1.replace('and if', 'when')[:-8])
            
        if characterID >= 4000000:
            characterKit.name += (' (<->)')
            
        os.system('cls')
        return characterKit
    else:
        print('Failed to retrieve character information.')
        return None

# Method for implementing custom card concepts, EZAs, etc.
def readCardFile(fileName):
    characterKit = Unit(characterID, '', '', 0, 0, 0, '', '', 0, 0, 0, 0, '', '', '', '', '', '',
    '', [], [0, 0, 0], [], [], [], [], [], [], [], [])
    with open(fileName, encoding="utf8") as file:
        count = 0
        for line in file:
            if line.__contains__('None'):
                count += 1
                continue
            match count:
                case 0: characterKit.id = int(line)
                case 1: characterKit.name = line[:-1]
                case 2: characterKit.rarity = line[:-1]
                case 3: characterKit.hp_max = int(line)
                case 4: characterKit.atk_max = int(line)
                case 5: characterKit.def_max = int(line)
                case 6: characterKit.element1 = line[:-1]
                case 7: characterKit.element2 = line[:-1]
                case 8: characterKit.eball_mod_mid = int(line)
                case 9: characterKit.eball_mod_mid_num = int(line)
                case 10: characterKit.eball_mod_max = int(line)
                case 11: characterKit.eball_mod_mid_num = int(line)
                case 12: characterKit.title = line[:-1]
                case 13: characterKit.leader_skill = line[:-1]
                case 14: characterKit.passive_skill_name = line[:-1]
                case 15: characterKit.active_skill_name = line[:-1]
                case 16: characterKit.active_skill_effect = line[:-1]
                case 17: characterKit.active_skill_condition = line[:-1]
                case 18: characterKit.passive_skill_itemized_desc = line[:-1]
                case 19:
                    characterKit.categories = line.split(', ')
                    if characterKit.categories:
                        characterKit.categories[len(characterKit.categories)-1] = characterKit.categories[len(characterKit.categories)-1][:-1]
                case 20:
                    characterKit.potential = line.split(', ')
                    print(f"0 - No Hidden Potential boost (0%)")
                    print(f"1 - {characterKit.potential[0]} (55%)")
                    print(f"2 - {characterKit.potential[1]} (69%)")
                    print(f"3 - {characterKit.potential[2]} (79%)")
                    print(f"4 - {characterKit.potential[3]} (90%)")
                    print(f"5 - {characterKit.potential[4][:-1]} (100%)")
                    hipo = int(input("Select Hidden Potential boost of unit (0-5): "))
                    
                    match hipo:
                        case 1:
                            characterKit.potential = characterKit.potential[0].split(' ')
                        case 2:
                            characterKit.potential = characterKit.potential[1].split(' ')
                        case 3:
                            characterKit.potential = characterKit.potential[2].split(' ')
                        case 4:
                            characterKit.potential = characterKit.potential[3].split(' ')
                        case 5:
                            characterKit.potential = characterKit.potential[4].split(' ')
                    characterKit.atk_max += int(characterKit.potential[0])
                    characterKit.def_max += int(characterKit.potential[1])
                    characterKit.hp_max += int(characterKit.potential[2])
                case 21:
                    specials = line.split('|')
                    for special in specials:
                        special = special.split('; ')
                        special[2] = int(special[2])
                        characterKit.specials.append(special)
                case 22: characterKit.transformations.append(line[:-1].split(', '))
                case 23: characterKit.costumes = line[:-1]
                case 24:
                    card_links = line[:-1].split('; ')
                    for card_link in card_links:
                        card_link = card_link.split(', ')
                        characterKit.card_links.append([card_link[0], card_link[1]])
                case 25: characterKit.finish_skills.append(line[:-1].split(', '))
                case 26: characterKit.standby_skills = line[:-1].split(', ')
                case 27: characterKit.dokkan_fields = line[:-1].split(', ')
            count += 1
    characterKit.passive_skill_itemized_desc = characterKit.passive_skill_itemized_desc.replace('\\n', '\n')

    os.system('cls')
    return characterKit

def main(characterID):
    if characterID == 0:        
        mainUnit = readCardFile(input('Add card .txt file here: '))
    else:
        mainUnit = getKit(characterID)
    
    print(f'{mainUnit.element1} {mainUnit.element2} {mainUnit.rarity} [{mainUnit.title}] {mainUnit.name}')
    print(f'\nLeader Skill: {mainUnit.leader_skill}')
    
    for special in zip(mainUnit.specials):
        print(f'\nSuper Attack: {special[0][0]} - {special[0][1]} (Ki from {special[0][2]})')
        if len(special[0]) > 3:
            if len(special[0]) > 4:
                print(f'- Condition: {special[0][4]}')
            print(f'- {special[0][3]}')
    
    print(f'\nPassive Skill: {mainUnit.passive_skill_name}')
    print(mainUnit.passive_skill_itemized_desc.replace('\n*', '\n\n*'))
    
    if mainUnit.costumes:
        print(f'\nCostume: {mainUnit.costumes}')
    
    if mainUnit.dokkan_fields:
        print(f'\nDomain Skill: {mainUnit.dokkan_fields[0]}')
        print(f'- {mainUnit.dokkan_fields[1]}')
    
    if mainUnit.active_skill_name:
        print(f'\nActive Skill: {mainUnit.active_skill_name}')
        print(f'- Effect: {mainUnit.active_skill_effect}')
        print(f'- Condition: {mainUnit.active_skill_condition}')
        
    if mainUnit.standby_skills:
        print(f'\nStandby Skill: {mainUnit.standby_skills[0]}')
        print(f'- Effect: {mainUnit.standby_skills[1]}')
        print(f'- Condition: {mainUnit.standby_skills[2]}')
        
    for finish_skill in mainUnit.finish_skills:
        print(f'\nFinish Skill: {finish_skill[0]}')
        print(f'- Effect: {finish_skill[1]}')
        print(f'- Condition: {finish_skill[2]}')
    
    print('\nLink Skills (Lv. 10):')
    print(mainUnit.card_links)
    print(f'\nCategories:\n{mainUnit.categories}')
    
    print('\nStats: ')
    print(f'HP: {mainUnit.hp_max} | ATK: {mainUnit.atk_max} | DEF: {mainUnit.def_max}')
    
    if not mainUnit.card_links:
        input("No partners available. Click any button to continue: ")
        calculateLinks(mainUnit, mainUnit)
    else:
        partnerID = input("Enter the Card ID of the partner character (Or leave empty to link character with self) (xxxxxxx): ")
        if partnerID == '':
            calculateLinks(mainUnit, mainUnit)
        else:
            partnerKit = getPartnerKit(int(partnerID))
            calculateLinks(mainUnit, partnerKit)
    
    if mainUnit.transformations:
        if len(mainUnit.transformations) == 1:
            input(f'Click any button to continue with transformed form ({mainUnit.transformations[0][1]}):')
            main(mainUnit.transformations[0][0])
        else:
            i = 0
            for transformation in mainUnit.transformations:
                print(f'{i} - {transformation}')
                i += 1
            transform = int(input(f'Select transformation (0-{i}) and continue with form): '))
            main(mainUnit.transformations[transform][0])
    else:
        input("Click any button to finish the program:")

os.system('cls') # Clears terminal; replace with os.system('clear') if on Unix/Linux/Mac
print("Welcome to Manila's Dokkan Calculator (Powered by Dokkan Wiki by ThievingSix)")
characterID = int(input("Enter the Card ID of the tested character (xxxxxxx): "))
main(characterID)