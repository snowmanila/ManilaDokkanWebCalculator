import copy
import inspect
import math
import os
import requests
import time # Time used for debugging

from dataclasses import dataclass, field

# Class for keeping track of a unit and its kit
@dataclass
class Unit:
    id: int
    unitClass: str
    type: str
    rank: str
    title: str
    name: str
    lead: str
    SANames: list
    SAEffects: list
    passiveName: str
    passive: str
    links: list
    linkBuffs: list
    categories: list
    stats: list
    kiValues: list
    kiMultiplier: int
    transform: int
    active: list
    
    def __init__(self, id, unitClass, type, rank, title, name, lead, SANames, 
    SAEffects, passiveName, passive, links, linkBuffs, categories, stats, 
    kiValues, kiMultiplier, transform, active):
        self.id = id
        self.unitClass = unitClass
        self.type = type
        self.rank = rank
        self.title = title
        self.name = name
        self.lead = lead
        self.SANames = SANames
        self.SAEffects = SAEffects
        self.passiveName = passiveName
        self.passive = passive
        self.links = links
        self.linkBuffs = linkBuffs
        self.categories = categories
        self.stats = stats
        self.kiValues = kiValues
        self.kiMultiplier = kiMultiplier
        self.transform = transform
        self.active = active
        
# Data Class for extra things post-transformation/exchange/etc.
@dataclass
class transformUtil:
    stackAvg: int
    standby: list
    domain: list
    
    def __init__(self, stackAvg, standby, domain):
        self.stackAvg = stackAvg
        self.standby = standby
        self.domain = domain
        
# Class for keeping track of a linking partner
@dataclass
class Partner:
    id: int
    type: str
    rank: str
    name: str
    links: list
    
    def __init__(self, id, type, rank, name, links):
        self.id = id
        self.type = type
        self.rank = rank
        self.name = name
        self.links = links
        
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

# Dev Note: Distinguish links to not be calculated SoT?
    # - Berserker - ATK +30% when HP is 50% or less
    # - Revival - Ki +2; ATK & DEF +5% and recovers 5% HP when HP is 50% or less
    # - Dodon Ray - ATK +15% when performing a Super Attack
    # - Kamehameha - ATK +10% when performing a Super Attack
    # - Warrior Gods - ATK +10%; plus an additional ATK +5% when performing a Super Attack
    # - Power Bestowed by God - ATK +10% when performing a Super Attack
    # - Limit-Breaking Form - ATK +10% when performing a Super Attack
    # - Legendary Power - ATK +15% when performing a Super Attack

# Dev Note: Rework API calls in future (Dokkan.wiki, incorporate with future team builder?)

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
# Dev Note: Adjust STR Buu's transformations (Multi-select?)
# Dev Note: Adjust TEQ LR Broly's EZA stacks (Multi-select?)

# Dev Note: Adjust stacking quantities in calculation, refer to additional documentation

# Retrieve leader skill
def retrieveLead(response, rank, EZA):
    lead = response[response.find('. | ')+4:response.find('name="description"')-2]
    if EZA == 1 or EZA == 2:
        i = 0
        while response.__contains__('leader_skill'):
            response = response[response.find('leader_skill')+12:]
            i += 1
        
            if rank == 'UR' and i == 8:
                break
            elif rank == 'LR' and i == 2:
                break
        lead = response[response.find('description&quot;:&quot;')+24:response.find('&quot;,&quot;effects')]            

    lead = lead.replace("\&quot;", "'")
    lead = lead.replace("&#39;", "'")
    lead = lead.replace("&amp;", "&")
    lead = lead.replace("+ ", "+")
    
    return lead

# Retrieve name of Super Attack
def retrieveSA(response, characterID, rank, EZA):
    if rank == 'LR':
        kiMultiplier = response[response.find('12,&quot;multiplier&quot;:')+26:response.find('},&quot;max')]
    else:
        kiMultiplier = response[response.find('12,&quot;multiplier&quot;:')+26:response.find('}},&quot;leader_skill')]
    SAContent = response[response.find('super_atks'):response.find('],&quot;passive_skill&quot;')]
    
    SANames = []
    SAEffects = []
    kiValues = []
    i = 0
    while SAContent.__contains__("secondary_effects"):
        SAContent = SAContent[SAContent.find(',&quot;name&quot;:&quot;')+24:]
        
        SAName = SAContent[:SAContent.find('&quot;,&quot;description')]
        if SAName.__contains__(',&quot;name&quot;:&quot;'):
            SAName = SAName[SAName.find(',&quot;name&quot;:&quot;')+24:]
        SAName = SAName.replace("\\n", "")
        SAName = SAName.replace("&amp;", "&")
        SAName = SAName.replace("&#39;", "'")
        SAName = SAName.replace("&quot;", "")
        
        SAContent = SAContent[SAContent.find('&quot;,&quot;description&quot;:&quot;')+37:]
        SAEffect = SAContent[:SAContent.find('&quot;,&quot;effects')]
        
        if SAEffect.__contains__(',&quot;description&quot;:&quot;'):
            SAEffect = SAEffect[SAEffect.find(',&quot;description&quot;:&quot;')+31:]
        
        if SAContent.__contains__("secondary_effects&quot;:[{"):
            SAContent = SAContent[SAContent.find(',&quot;name&quot;:&quot;')+24:]
            effect = SAContent[:SAContent.find('&quot;,&quot;description&quot;:&quot;')]
            
            # Dev Note: Fix SA transformations for post-EZA kits (INT Buuhan, etc.)
            if SAContent.__contains__('Super Attack Transformation &quot;,&quot;description&quot;:&quot;'):
                effect = SAContent[SAContent.find('Super Attack Transformation &quot;,&quot;description&quot;:&quot;')+65:SAContent.find('&quot;,&quot;lv')]
            if SAContent.__contains__('Super Attack Transformation&quot;,&quot;description&quot;:&quot;') and EZA != 0:
                effect = SAContent[SAContent.find('Super Attack Transformation&quot;,&quot;description&quot;:&quot;')+64:SAContent.find('&quot;,&quot;lv')]
            if not effect.__contains__(',&quot;name&quot;:&quot;'):
                SAEffect += f" ({effect})"
        SAEffect = SAEffect.replace("\\n", "")
        SAEffect = SAEffect.replace("&amp;", "&")
        SAEffect = SAEffect.replace("&#39;", "'")
        SAEffect = SAEffect.replace("&quot;", "")
        SAEffect = SAEffect.replace(" )", ")")
        
        if SAEffect.__contains__('aises ATK and raises DEF for 1 turn'):
            SAEffect = SAEffect.replace('aises ATK and raises DEF for', 'aises ATK for 1 turn, raises DEF for')
                
        if (characterID == 1001401 or characterID == 1003341 or
        characterID == 2000231 or (characterID == 1008531 and EZA == 0)):
            SAEffect = SAEffect.replace('Greatly raises ATK', 'Raises ATK by 67%')
        elif characterID == 1010061:
            SAEffect = SAEffect.replace(' and raises ATK for 1 turn', '')
            SAEffect = SAEffect.replace('Causes ', 'Raises ATK by 30% for 1 turn and causes ')
        elif characterID == 1010071 and EZA == 0:
            SAEffect = SAEffect.replace('Causes mega-colossal damage to enemy and greatly raises ATK for 1 turn', 'Raises ATK by 50% for 1 turn and causes mega-colossal damage to enemy')
        elif SAEffect.__contains__('Raises ATK & DEF for '):
            SAEffect = SAEffect.replace(f'Raises ATK & DEF ', 'Raises ATK & DEF by 30% ')
        elif ((SAEffect.__contains__('Raises ATK & DEF ') or
        SAEffect.__contains__('Raises ATK & DEF, ')) and
        not SAEffect.__contains__('Raises ATK & DEF by ')):
            if SAEffect.__contains__('extreme damage'):
                # Dev Note: WHAT DO YOU MEAN EXTREME DAMAGE MULTIPLIERS HAVE 10% STACKING
                # AS COMPARED TO EVERYTHING ELSE THAT HAS 20%???
                SAEffect = SAEffect.replace(f'Raises ATK & DEF', 'Raises ATK & DEF by 10%')
            else:
                SAEffect = SAEffect.replace(f'Raises ATK & DEF', 'Raises ATK & DEF by 20%')
        elif ((SAEffect.__contains__('Raises ATK') or SAEffect.__contains__('Lowers own ATK')) and
        not SAEffect.__contains__(' by ')):
            SAEffect = SAEffect.replace(f'aises ATK', 'aises ATK by 30%')
            SAEffect = SAEffect.replace(f'Lowers own ATK', 'Raises ATK by -30%')
        elif (SAEffect.__contains__('Greatly raises ATK') or
        SAEffect.__contains__('greatly raising ATK ') or
        SAEffect.__contains__('ATK & DEF being greatly raised')):
            SAEffect = SAEffect.replace(f'Greatly raises ATK and raises DEF ', 'Raises ATK by 50% for 1 turn, raises DEF by 30% ')
            SAEffect = SAEffect.replace(f'Greatly raises ATK & DEF ', 'Raises ATK & DEF by 50% ')
            SAEffect = SAEffect.replace(f'Greatly raises ATK', 'Raises ATK by 50%')
            SAEffect = SAEffect.replace(f'greatly raises ATK', 'raises ATK by 50%')
            SAEffect = SAEffect.replace(f'greatly raising ATK ', 'raising ATK by 50% ')
            SAEffect = SAEffect.replace(f'ATK & DEF being greatly raised', 'raises ATK & DEF by 50%')
        elif SAEffect.__contains__('assively raises ATK') or SAEffect.__contains__('Massively raises DEF'):
            SAEffect = SAEffect.replace(f'Massively raises ATK & DEF', 'Raises ATK & DEF by 100%')
            SAEffect = SAEffect.replace(f'Massively raises DEF', 'Raises DEF by 100%')
            SAEffect = SAEffect.replace(f'Massively raises ATK', 'Raises ATK by 100%')
            SAEffect = SAEffect.replace(f'massively raises ATK', 'raises ATK by 100%')
        elif (SAEffect.__contains__(' and raises ATK ') and
        SAEffect.__contains__(' turn')):
            SARaise = 'R' + SAEffect[SAEffect.find(' and raises ATK ')+6:]
            SARaise = SARaise[:SARaise.find(' turn')+6]
            
            SAEffect = SAEffect.replace(f' and r{SARaise[1:]}', '')
            SAEffect = f'{SARaise}, {SAEffect}'.replace(', Causes', ' and causes')
            SAEffect = SAEffect.replace(f'Raises ATK & DEF for ', 'Raises ATK & DEF by 50% for ')
            SAEffect = SAEffect.replace(f'Raises ATK for ', 'Raises ATK by 50% for ')
        elif (SAEffect.__contains__('; raises ATK ') and
        SAEffect.__contains__(' turn')):
            SARaise = 'R' + SAEffect[SAEffect.find('; raises ATK ')+3:]
            SARaise = SARaise[:SARaise.find(' turn')+6]
            
            SAEffect = SAEffect.replace(f'; r{SARaise[1:]}', '')
            SAEffect = f'{SARaise}, {SAEffect}'.replace(', Causes', ' and causes')
            SAEffect = SAEffect.replace(f'Raises ATK & DEF for ', 'Raises ATK & DEF by 50% for ')
            SAEffect = SAEffect.replace(f'Raises ATK for ', 'Raises ATK by 50% for ')
        elif (SAEffect.__contains__(' and raises DEF ') and
        SAEffect.__contains__(' turn')):
            SARaise = 'R' + SAEffect[SAEffect.find(' and raises DEF ')+6:]
            SARaise = SARaise[:SARaise.find(' turn')+6]
            
            SAEffect = SAEffect.replace(f' and r{SARaise[1:]}', '')
            SAEffect = SAEffect.replace(f'Causes ', f'{SARaise} and causes ')
            SAEffect = SAEffect.replace(f', causes ', f', {SARaise} and causes ')
            SAEffect = SAEffect.replace(f'Raises DEF for ', 'Raises DEF by 50% for ')
            SAEffect = SAEffect.replace(f'Raises ATK for ', 'Raises ATK by 30% for ')
            SAEffect = SAEffect.replace(f', Raises', ', raises')
        elif (SAEffect.__contains__(' and ATK ') and
        SAEffect.__contains__(' turns')):
            SARaise = SAEffect[SAEffect.find(' and ATK ')+6:]
            SARaise = SARaise[:SARaise.find(' turns')+6]
            
            SAEffect = SAEffect.replace(f' and A{SARaise}', '')
            SAEffect = SAEffect.replace(f'Causes ', f'Raises A{SARaise} and causes ')
            SAEffect = SAEffect.replace(f'Raises ATK for ', 'Raises ATK by 50% for ')
            SAEffect = SAEffect.replace(' +', ' by ')
        elif (SAEffect.__contains__(' and DEF ') and
        SAEffect.__contains__(' turns')):
            SARaise = SAEffect[SAEffect.find(' and DEF ')+6:]
            SARaise = SARaise[:SARaise.find(' turns')+6]
            
            SAEffect = SAEffect.replace(f' and D{SARaise}', '')
            SAEffect = SAEffect.replace(f'Causes ', f'Raises D{SARaise} and causes ')
            SAEffect = SAEffect.replace('+', 'by ')
         
        if (SAEffect.__contains__("damage, allies' ATK +")):
            SAEffect = SAEffect.replace(", allies' ATK ", " to enemy; raises allies' ATK by ")
            SAEffect = SAEffect.replace(" +", " ")
        elif (SAEffect.__contains__("and allies' ATK +")):
            SAEffect = SAEffect.replace(" and allies' ATK +", "; raises allies' ATK by ")
        elif SAEffect.__contains__('and all allies'):
            SAEffect = SAEffect.replace(" and all allies' ", "; raises allies' ")
            SAEffect = SAEffect.replace(" +", " by ")
        elif (SAEffect.__contains__('and raises ') and
        SAEffect.__contains__(' allies')):
            SAEffect = SAEffect.replace(' and raises ', '; raises ')
            SAEffect = SAEffect.replace(" +", " ")
        elif (SAEffect.__contains__('; ATK +') and
        SAEffect.__contains__('for allies ')):
            SAEffect = SAEffect.replace(' ATK +', " raises allies' ATK by ")
            SAEffect = SAEffect.replace(' for allies ', ' ')
        elif (SAEffect.__contains__("; ") and
        SAEffect.__contains__("allies' ") and not
        SAEffect.__contains__("raises allies' ")):
            SAEffect = SAEffect.replace('; ', '; raises ')
            SAEffect = SAEffect.replace(' +', ' by ')
            SAEffect = SAEffect.replace('raises raises', 'raises')
        elif (SAEffect.__contains__(", ATK +") and
        SAEffect.__contains__("% for all allies ")):
            SAEffect = SAEffect.replace(', ATK +', "; raises all allies' ATK by ")
            SAEffect = SAEffect.replace('for all allies ', '')
        elif SAEffect.__contains__("; DEF +"):
            DEFRaise = SAEffect.split('; ')[1]
            SAEffect = SAEffect[0].lower() + SAEffect[1:]
            SAEffect = "Raises " + DEFRaise + " and " + SAEffect.replace(f'; {DEFRaise}', '')
            SAEffect = SAEffect.replace('+', 'by ')
        elif characterID == 1008811 or characterID == 1008821:
            SAEffect = SAEffect.replace(' and raises ATK & DEF', '')
            SAEffect = SAEffect.replace('Causes', 'Raises ATK & DEF by 20% and causes')
        elif characterID == 1008081:
            SAEffect = SAEffect.replace(' and greatly raises ATK', '')
            SAEffect = SAEffect.replace('Causes', 'Raises ATK by 50% and causes')
        SAEffect = SAEffect.replace(', causes', ' and causes')
        
        if SAEffect.__contains__('Raises DEF'):
            SAEffect = SAEffect.replace(f'Raises DEF', 'Raises DEF by 30%')
        if SAEffect.__contains__('reatly raises DEF'):
            SAEffect = SAEffect.replace(f', Greatly raises DEF', ', raises DEF by 50%')
            SAEffect = SAEffect.replace(f'Greatly raises DEF', 'Raises DEF by 50%')
            SAEffect = SAEffect.replace(f'greatly raises DEF', 'raises DEF by 50%')
        #elif SAEffect.__contains__('enemy and raises DEF '):
            #SARaise = 'R' + SAEffect[SAEffect.find('enemy and ')+11:SAEffect.find('turn')+4]
            #SAEffect = f'{SARaise} and {SAEffect.replace(SARaise, "")}'
            #SAEffect = SAEffect.replace('and Causes', 'and causes')
        elif SAEffect.__contains__('DEF being reduced'):
            SAEffect = SAEffect.replace(f'DEF being reduced', 'raises DEF by -30%')
            
        if not SAEffect.__contains__(' damage to enemy'):
            SAEffect = SAEffect.replace('damage', 'damage to enemy')
        if not SAEffect.__contains__('auses'):
            SAEffect = ("Causes " + SAEffect)
            SAEffect = SAEffect[:7] + SAEffect[7:8].lower() + SAEffect[8:]
            
        if SAEffect.__contains__(', raises DEF ') and not SAEffect.__contains__(', raises DEF by '):
            SAEffect = SAEffect.replace(', raises DEF ', ', raises DEF by 30% ')
            
        if SAEffect.__contains__('(Super Attack by '):
            SAEffect = SAEffect.replace('(Super Attack by ', '(Super Attack +')
        SAEffect = SAEffect.replace('(Super Attack 30', '(Super Attack +30')
        
        SAContent = SAContent[SAContent.find(';ki&quot;:')+10:]
        kiValue = SAContent[:SAContent.find(',&quot;lv')]
        
        if SAEffect.__contains__('Required Ki -'):
            subKi = SAEffect.split('Required Ki -')[1]
            subKi = int(subKi.split(' for launching Super')[0])
            kiValue = str(int(kiValue) - subKi)
        elif SAEffect.__contains__('Launches Super Attack when Ki is '):
            subKi = SAEffect.split('Launches Super Attack when Ki is ')[1]
            subKi = int(subKi.split(' or more')[0])
            kiValue = str(subKi)
        
        if EZA != 0 and SAName.__contains__('(Extreme)'):
            #if "effect" in locals():
            #    SAEffect += effect
            SANames[i] = SAName
            SAEffects[i] = SAEffect
            kiValues[i] = kiValue
            i += 1
        elif SAName.__contains__('(Extreme)'):
            return SANames, SAEffects, kiValues, kiMultiplier
        elif int(kiValue) not in kiValues:
            SANames.append(SAName)
            SAEffects.append(SAEffect)
            kiValues.append(int(kiValue))
        
        SAContent = SAContent[SAContent.find("},{&quot;id&quot;:")+17:]
    return SANames, SAEffects, kiValues, kiMultiplier

# Retrieve name of Passive Skill
def retrievePassive(response, rank, EZA):
    response = response[response.find('passive_skill'):]
    
    # Fixes EZA/SEZA passives for rage/giant forms
    if ((not response.__contains__('passive_skill&quot;:null}')) and 
    response.__contains__('passive_skill&quot;:null,') and EZA == 0):
        return 'None', '- None'
    elif (response.__contains__('passive_skill&quot;:null}') and EZA != 2):
        return 'None', '- None'
    
    passiveName = response[response.find(',&quot;name&quot;:&quot;')+24:response.find('&quot;,&quot;description&quot;')]
    passiveName = passiveName.replace("&#39;", "'")
    passiveName = passiveName.replace("\&quot;", '"')
    
    if EZA == 1:
        i = 0
        while response.__contains__('description_itemized'):
            response = response[response.find('description_itemized')+20:]
            i += 1
        
            if rank == 'UR' and i == 8:
                break
            elif rank == 'LR' and i == 4:
                break
    elif EZA == 2:
        i = 0
        while response.__contains__('description_itemized'):
            response = response[response.find('description_itemized')+20:]
        
            if rank == 'UR' and i == 8:
                print(response[:1000])
            elif rank == 'LR' and i == 4:
                print(response[:1000])
                
    response = response[response.find('[{&quot;description&quot;:&quot;')+1:]
    passive = response[:response.find('&quot;]}],&quot;')]
    
    passive = passive.replace('{&quot;description&quot;:&quot;', "*")
    passive = passive.replace('&quot;,&quot;effects&quot;:', ":\n")
    passive = passive.replace('[&quot;', '- ')
    passive = passive.replace('&quot;,&quot;', '\n- ')
    passive = passive.replace('&quot;]},','\n\n')
    passive = passive.replace("\\n", "")
    passive = passive.replace("&amp;", "&")
    passive = passive.replace("&#39;", "'")
    passive = passive.replace("&quot;", "")
    passive = passive.replace("\\", "'")
    passive = passive.replace("  ", " ")
    
    passive = passive.replace("granting deadly power to attack", "ATK 1000000%{passiveImg:up_g}")
    passive = passive.replace(" (count starts from the ", ", starting from the ")
    passive = passive.replace("{passiveImg:atk_down}", "ATK Down")
    passive = passive.replace("{passiveImg:def_down}", "DEF Down")
    passive = passive.replace("{passiveImg:stun}", "Stunned")
    passive = passive.replace("{passiveImg:astute}", "Sealed")
    passive = passive.replace(" and performs a critical hit", "\n- Performs a critical hit")

    return passiveName, passive

# Retrieve Linkset
def retrieveLinks(response):
    response = response[response.find('link_skills&quot'):]

    links = []
    linkBuffs = []
    while response.__contains__("lv&quot;:10"):
        response = response[response.find('&quot;name&quot;:&quot;')+23:]
        link = response[:response.find('&quot;,&quot;')]
        link = link.replace("\\n", "")
        link = link.replace("&amp;", "&")
        link = link.replace("&#39;", "'")
        link = link.replace("&quot;", "")
        links.append(link)
        
        response = response[response.find('lv&quot;:10')+42:]
        linkBuff = response[:response.find('&quot;}]}')]
        linkBuff = linkBuff.replace("\\n", "")
        linkBuff = linkBuff.replace("&amp;", "&")
        linkBuff = linkBuff.replace("&#39;", "'")
        linkBuff = linkBuff.replace("&quot;", "")
        linkBuffs.append(linkBuff)

    return links, linkBuffs

# Retrieve Categories of unit
def retrieveCategories(response):   
    response = response[response.find('],&quot;categories'):response.find('support&quot;:[]}}],&quot;a')]
    if response.__contains__('categories&quot;:[]'):
        return []

    categories = []
    while response.__contains__("&quot;name&quot;:&quot;"):
        response = response[response.find('&quot;name&quot;:&quot;')+23:]
        category = response[:response.find('&quot;,&quot;characters')]
        category = category.replace("&#39;", "'")
        
        categories.append(category)

    return categories

# Retrieve HP, ATK, and DEF stats of unit
def retrieveStats(response, characterID, EZA, rank):
    response = response[response.find(',&quot;hp&quot;:'):]   
    stats = []
    
    response = response[response.find(',&quot;max&quot;:')+17:] 
    hpMax = int(response[:response.find(',&quot;eza&quot;:')])
    response = response[response.find(',&quot;eza&quot;:')+17:]
    hpEZA = int(response[:response.find('},')])
    stats.append(hpMax)
    
    response = response[response.find(',&quot;max&quot;:')+17:] 
    atkMax = int(response[:response.find(',&quot;eza&quot;:')])
    response = response[response.find(',&quot;eza&quot;:')+17:]
    atkEZA = int(response[:response.find('},')])
    stats.append(atkMax)
    
    response = response[response.find(',&quot;max&quot;:')+17:] 
    defMax = int(response[:response.find(',&quot;eza&quot;:')])
    response = response[response.find(',&quot;eza&quot;:')+17:]
    defEZA = int(response[:response.find('},')])
    stats.append(defMax)
    
    if EZA != 0 and rank != 'LR':
        stats[0] = hpEZA
        stats[1] = atkEZA
        stats[2] = defEZA

    if not response.__contains__('hidden_potential&quot;:null'):
        response = response[response.find('hidden_potential&quot;:'):]

        response = response[response.find('&quot;hp&quot;:')+15:]
        hpHIPO = int(response[:response.find(',&quot;atk&quot;:')])
        stats[0] += hpHIPO
        
        response = response[response.find(',&quot;atk&quot;:')+17:] 
        atkHIPO = int(response[:response.find(',&quot;def&quot;:')])
        stats[1] += atkHIPO
        
        response = response[response.find(',&quot;def&quot;:')+17:] 
        defHIPO = int(response[:response.find('}')])
        stats[2] += defHIPO
    elif rank == "SSR" or rank == "UR" or rank == "LR":
        response = response[response.find('base_character_id&quot;:')+24:]
        originID = response[:response.find(',&quot;base_character')]
        if rank == "SSR" and int(originID) % 2 == 0:
            originID = originID[:-1] + "1"
        
        originResponse = (requests.get(f'https://dokkan.fyi/characters/{originID}')).text
        originResponse = originResponse[originResponse.find('hidden_potential&quot;:'):]

        originResponse = originResponse[originResponse.find('&quot;hp&quot;:')+15:]
        hpHIPO = int(originResponse[:originResponse.find(',&quot;atk&quot;:')])
        
        originResponse = originResponse[originResponse.find(',&quot;atk&quot;:')+17:] 
        atkHIPO = int(originResponse[:originResponse.find(',&quot;def&quot;:')])
        
        originResponse = originResponse[originResponse.find(',&quot;def&quot;:')+17:] 
        defHIPO = int(originResponse[:originResponse.find('}')])
        
        response = response[response.find(f'&quot;id&quot;:{characterID}')+15:]

        response = response[response.find(',&quot;max&quot;:')+17:]
        hpMax = response[:response.find('},&quot;atk&quot;:{')]
        if EZA == 0:
            hpMax = int(hpMax[:hpMax.find(',&quot;eza&quot;:')])
        else:
            hpMax = int(hpMax[hpMax.find(',&quot;eza&quot;:')+17:])
        stats[0] = hpMax + hpHIPO
            
        response = response[response.find(',&quot;max&quot;:')+17:]
        atkMax = response[:response.find('},&quot;atk&quot;:{')]
        if EZA == 0:
            atkMax = int(atkMax[:atkMax.find(',&quot;eza&quot;:')])
        else:
            atkMax = atkMax[atkMax.find(',&quot;eza&quot;:')+17:]
            atkMax = int(atkMax[:atkMax.find('},&quot;def')])
        stats[1] = atkMax + atkHIPO
            
        response = response[response.find(',&quot;max&quot;:')+17:]
        defMax = response[:response.find('},&quot;atk&quot;:{')]
        if EZA == 0:
            defMax = int(defMax[:defMax.find(',&quot;eza&quot;:')])
        else:
            defMax = defMax[defMax.find(',&quot;eza&quot;:')+17:]
            defMax = int(defMax[:defMax.find('},&quot;ki_multipliers')])
        stats[2] = defMax + defHIPO

    return stats

def calcActiveATK(active, ATK, activeATK, onAttackATK, crit, superEffective,
rank, SANames, SAEffects, kiValues, kiMultiplier, additional):
    buff = 0
    flat = True
    if active:
        if active[1].__contains__('critical hit'):
            crit = True
        
        if (active[1].__contains__('ATK ') and active[1].__contains__('% ') and
        not active[1].__contains__('damage to enemy') and not active[1].__contains__('sacrificing ')):
            buff = active[1].split('ATK ')[1]
            
            if active[1].__contains__(" allies' ATK by"):
                buff = buff.split('by ')[1]
            
            if buff.__contains__('% ') or buff.__contains__('%,'):
                flat = False
                if buff.__contains__('& DEF +'):
                    buff = buff.split('& DEF +')[1]
                buff = int(buff.split('%')[0])
            else:
                buff = int(buff.split(' ')[0])
            print(f'{ATK} (Before Activating Active Skill: "{active[0]}")')
                
            calcActiveATK([], ATK, activeATK, onAttackATK, crit, 
            superEffective, rank, SANames, SAEffects, kiValues, kiMultiplier, additional)
                
            if flat:
                ATK = int(ATK + buff)
                print(f'{ATK} (With {buff} Flat Buff, After Activating Active Skill: "{active[0]}")')
            else:
                ATK = int(ATK * (1 + (buff/100)))
                print(f'{ATK} (With {buff}% Buff, After Activating Active Skill: "{active[0]}")')
            
            calcActiveATK([], ATK, activeATK, onAttackATK, crit, 
            superEffective, rank, SANames, SAEffects, kiValues, kiMultiplier, additional)
    
    baseSAName = SANames[kiValues.index(min(kiValues))]
    baseSAEffect = SAEffects[kiValues.index(min(kiValues))]
    baseKiValue = kiValues[kiValues.index(min(kiValues))]
    
    for SAName, SAEffect, kiValue in zip(SANames, SAEffects, kiValues):
        newKiMultiplier = (int(kiMultiplier)/24)*(12+int(kiValue))
        ATKnew = int(ATK * (newKiMultiplier/100)) # Apply Ki multiplier
        print(f'{ATKnew} (With {newKiMultiplier}% Ki Multiplier)')        
        if SANames[0] == "None":
            print("No Super Attack Available\n")
            return
        
        print(f"Launching Super Attack: {SAName} at {kiValue} Ki")
        baseATK = int(ATK * ((int(kiMultiplier)/24)*(12+int(kiValues[0]))/100))
        calcATKSA(kiValue, SAName, SAEffect, ATKnew, onAttackATK, 0, 0, "", crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
    if int(kiValue) < 12 and 12 not in kiValues:
        ATKnew = int(ATK * (int(kiMultiplier)/100)) # Apply Ki multiplier
        print(f'{ATKnew} (With {kiMultiplier}% Ki Multiplier)')
        print(f"Launching Super Attack: {SAName} at 12 Ki")
        baseATK = int(ATK * ((int(kiMultiplier)/24)*(12+int(kiValues[0]))/100)) # Apply Ki multiplier
        calcATKSA(12, SAName, SAEffect, ATKnew, onAttackATK, 0, 0, "", crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
    if rank == "LR" and int(kiValue) < 18:
        print(f'{ATKnew} (With {(((200-int(kiMultiplier))/2)+int(kiMultiplier))}% Ki Multiplier)')
        print(f"Launching Super Attack: {SAName} at 18 Ki")
        ATKnew = int(ATK * ((((200-int(kiMultiplier))/2)+int(kiMultiplier))/100)) # Apply Ki multiplier
        calcATKSA(18, SAName, SAEffect, ATKnew, onAttackATK, 0, 0, "", crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
    if rank == "LR":
        print(f'{ATKnew} (With 200% Ki Multiplier)')
        print(f"Launching Super Attack: {SAName} at 24 Ki")
        ATKnew = int(ATK * 2) # Apply Ki multiplier
        calcATKSA(24, SAName, SAEffect, ATKnew, onAttackATK, 0, 0, "", crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)

# Calculate ATK stat given 'on attack' conditions (When attacking, per attack
# evaded/received/performed, when the target enemy ..., etc.)
def calcATKSA(ki, SAName, SAEffect, ATK, onAttackATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK):
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
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
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
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif condition.__contains__("Once only") or condition.__contains__("once only"):
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
            print("ATK (After one-time buff):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif (condition.__contains__("After delivering a final blow") or
            condition.__contains__("a final blow is delivered")):
            print("ATK (Before delivering a final blow):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif (condition.__contains__("When attacking a") and
        condition.__contains__(" enemy")):
            print(f"ATK {condition}")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
            condition = condition.replace('When attacking a', 'When not attacking a')
            print(f"ATK {condition}")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif (condition.__contains__("When there is a") and
        condition.__contains__(" enemy")):
            print(f"ATK {condition}")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
            condition = condition.replace('When there is a', 'When there is not a')
            print(f"ATK {condition}")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("receiving an attack"):
            print("ATK (Before receiving an attack):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("receiving or evading an attack"):
            print("ATK (Before receiving or evading an attack):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("evading an attack"):
            print("ATK (Before evading an attack):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__('After guard is activated'):
            print('ATK (Before guard is activated):')
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            condition = condition.replace(', or ', ', for ')
            print(f'ATK {condition}:')
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif condition.__contains__('Whenever guard is activated'):
            if not condition.__contains__('(up to') and not "limit" in locals():
                limit = buff
            
            print(f'ATK (Before guard is activated):')
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            
            for i in range(1, int(limit/buff)+1):
                if i == 1:
                    print(f'ATK (Guard activated {i} time):')
                else:
                    print(f'ATK (Guard activated {i} times):')
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (buff*i), newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff + (buff*i), newSAFlatBuff])
        elif condition.__contains__('henever guard is activated'):
            limit = buff
            if condition.__contains__('(up to'):
                limit = condition.split('(up to ')[1]
                limit = int(limit.split('%')[0])
                print(limit/buff)
                   
            condition = condition.replace('are on the', 'are not on the')
            condition = condition.replace(condition[condition.find('whenever'):], '')
            print(f'ATK {condition}before guard is activated):')
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            
            condition = condition.replace('are not on the', 'are on the')
            for i in range(1, int(limit/buff)+1):
                if i == 1:
                    print(f'ATK {condition}guard activated {i} time:')
                else:
                    print(f'ATK {condition}guard activated {i} times:')
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (buff*i), newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff + (buff*i), newSAFlatBuff])
        elif condition.__contains__("he more HP remaining"):
            for i in range(0, 101):
                if i % 10 == 0:
                    print("ATK at " + str(i) + "% HP:")
                    if flat:
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff,  int(saFlatBuff + (int(buff)*(i/100))), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff, int(saFlatBuff + (int(buff)*(i/100)))])
                    else:
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, int(saPerBuff + (int(buff)*(i/100))), newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, int(saPerBuff + (int(buff)*(i/100))), saFlatBuff])
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
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
                else:
                    print(f"ATK (Before performing {cond}):")
                    #calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    #print(f"ATK (After performing {cond}):")
                    #calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            else:
                buff = buff*(ki/kiLimit)
                if flat:
                    newSAFlatBuff = saFlatBuff + (buff)
                else:
                    newSAPerBuff = saPerBuff + (buff)
                print(f'ATK (With {ki} Ki):')
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
        elif condition.__contains__("For every Rainbow Ki Sphere obtained"):
            if flat:
                print("ATK (With 0 Rainbow Ki Spheres obtained):")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*2.5), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*5), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            else:
                print("ATK (With 0 Rainbow Ki Spheres obtained):")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*2.5), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*5), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("or every "):
            cond = (condition.split('or every ')[1]).replace(',', '')
            if condition.__contains__(', for') and not condition.__contains__('ttack performed, for'):
                cond2 = condition.replace(', for every attack performed', '')
                cond2 = cond2.replace('hen there is', 'hen there is not')
                print(f"ATK {cond2}:")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            elif not condition.__contains__('performed'):
                cond = cond.replace('ttack ', 'ttacks ')
                print(f'ATK (With 0 {cond}:')
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
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
                            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff + (buff*i), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, saFlatBuff + (buff*i)])
                        else:
                            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (buff*i), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff + (buff*i), newSAFlatBuff])
                else:
                    turnLimit = additional+2
                    if (SAEffect.__contains__('Raises ATK by') and
                    SAEffect.__contains__('% for ') and
                    SAEffect.__contains__(' turns ')):
                        turnLimit = SAEffect.split(' for ')[1]
                        turnLimit = int(turnLimit.split(' turns ')[0])
                        turnLimit = max((math.ceil(turnLimit/2))*(additional+1), 35)
                    
                    for i in range(1, turnLimit):
                        if i == 1:
                            print(f'ATK (With {str(i)} {cond}:')
                        else:
                            cond = cond.replace('ttack ', 'ttacks ')
                            print(f'ATK (With {str(i)} {cond}:')
                        if flat:
                            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff + (buff*i), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff, saFlatBuff + (buff*i)])
                        else:
                            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (buff*i), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff + (buff*i), saFlatBuff])
            else:
                for i in range(1, int(limit/buff)+1):
                    if i == 1:
                        print(f'ATK (With {str(i)} {cond}):')
                    else:
                        cond = cond.replace('ttack ', 'ttacks ')
                        print(f'ATK (With {str(i)} {cond}):')
                    if flat:
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff + (buff*i), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff, saFlatBuff + (buff*i)])
                    else:
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (buff*i), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff + (buff*i), saFlatBuff])
                if limit % buff != 0:
                    print(f'ATK (With {str(i+1)} {cond}):')
                    if flat:
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff + limit, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff, saFlatBuff + limit])
                    else:
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + limit, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, saPerBuff + limit, saFlatBuff])
        elif (condition.__contains__(" there is another") and
        condition.__contains__("Category ally ")):
            category = condition.split("another '")[1]
            category = category.split("' Category")[0]
                
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, [activeATK, newSAPerBuff, newSAFlatBuff])
            
            condition = condition.replace('there is', 'there is not')
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("Category ally attacking in the same turn"):
            if condition.__contains__(' Per '):
                category = condition.split(" Per ")[1]
            else:
                category = condition.split(" per ")[1]
            category = category.split(" Category")[0]
                
            if condition.__contains__("self excluded"): 
                for i in range(0, 3):
                    print("ATK (When attacking, with " + str(i) + " " + category + " Category allies in the same turn):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (i * buff), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            else:
                for i in range(1, 4):
                    print("ATK (When attacking, with " + str(i) + " " + category + " Category allies in the same turn):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (i * buff), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("Starting from the ") and condition.__contains__(" turn from the "):
            turn = condition.replace('Starting from ', 'Before ')
            turn = turn.replace('chance', 'chance not activated')
            print(f"ATK {turn}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("turn(s)"):
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK (After turn buff):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("When the target enemy is "):
            condition = condition.replace("{passiveImg:atk_down}", "ATK Down")
            condition = condition.replace("{passiveImg:def_down}", "DEF Down")
            condition = condition.replace("{passiveImg:stun}", "Stunned")
            condition = condition.replace("{passiveImg:astute}", "Sealed")
            
            print("ATK (Without status condition):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("After performing ") and (condition.__contains__("ttack(s) in battle") or
        condition.__contains__("ttacks in battle")):
            cond = condition.split("After performing ")[1]
            
            print(f"ATK (Before performing {cond}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK (After performing {cond}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("Every time the character performs ") and condition.__contains__("ttacks in battle"):
            cond = condition.split("Every time the character performs ")[1]
            
            print(f"ATK (Before performing {cond.split(',')[0]}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK (For every {cond.replace('attacks', 'attacks performed')}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif (condition.__contains__("After receiving ") and 
        (condition.__contains__("ttacks in battle") or condition.__contains__("ttack(s) in battle"))):
            cond = condition.split("After receiving ")[1]
            
            print(f"ATK (Before receiving {cond}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK (After receiving {cond}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)        
        elif condition.__contains__("After evading ") and condition.__contains__("ttacks in battle"):
            cond = condition.split("After evading ")[1]
            
            print(f"ATK (Before evading {cond}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK (After evading {cond}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("For every Ki when attacking"):
            if limit/buff <= ki:
                if flat:
                    newSAFlatBuff = saFlatBuff + limit
                else:
                    newSAPerBuff = saPerBuff + limit
                print(f"ATK (With 12 Ki):")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            else:
                print(f"ATK (Before performing {cond}):")
                #calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                #print(f"ATK (After performing {cond}):")
                #calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__(" your team has ") and condition.__contains__("attacking in the same turn"):
            cond = condition.split(" your team has ")[0]
            ally = condition.split("your team has ")[1]
            
            print(f"ATK ({cond} your team has {ally}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            print(f"ATK ({cond} your team doesn't have {ally}):")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
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
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff + (i * buff), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                else:
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff + (i * buff), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif (condition.__contains__("When there is a")):
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            condition = condition.replace('When there is a', 'When there is not a')
            condition = condition.replace('when attacking with', 'when not attacking with')
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("per Ki Sphere obtained"):
            condition = condition.split(', per')[0]
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*3), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*7.5), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK {condition}, with 23 (Max) Ki Spheres Obtained):")
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*23), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    print(f"ATK {condition}, with {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                else:
                    print(f"ATK {condition}, with {3 + kiStart} Ki Spheres Obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*3), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    print(f"ATK {condition}, with {7.5 + kiStart} (AVG) Ki Spheres obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*7.5), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    print(f"ATK {condition}, with {23 - kiStart} (Max) Ki Spheres obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff+(buff*23), counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*3), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*7.5), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK {condition}, with 23 (Max) Ki Spheres Obtained):")
                        calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*23), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    print(f"ATK {condition}, with {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                else:
                    print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*3), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*7.5), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
                    print(f"ATK {condition}, with 23 (Max) Ki Spheres obtained):")
                    calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff+(buff*23), saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        elif condition.__contains__("When attacking with ") and condition.__contains__(" Ki)"):
            kiATK = condition.split("When attacking with ")[1]
            kiATK = int(kiATK.split(" ")[0])
            if ((condition.__contains__("or more") and int(ki) < kiATK) or
            (condition.__contains__("or less") and int(ki) > kiATK)):
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
            else:
                print(f"ATK {condition}:")
                calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
        else:
            print(f"ATK {condition}:")
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, newSAPerBuff, newSAFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
    
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
            calcATKSA(ki, SAName, SAEffect, ATK, copyATK, saPerBuff, saFlatBuff, counter, crit, superEffective, additional, rank, baseSAName, baseSAEffect, baseKiValue, baseATK, active, activeATK)
    else:        
        ATK = int(ATK * (1 + (saPerBuff/100))) # Apply 'on attack' percentage buffs
        print(f"{ATK} (With {saPerBuff}% 'On Attack' Passive Buff)")
        ATK = int(ATK + saFlatBuff) # Apply 'on attack' flat buffs
        print(f"{ATK} (With {saFlatBuff} Flat 'On Attack' Passive Buff)")
        
        baseATK = int(baseATK * (1 + (saPerBuff/100))) # Apply 'on attack' percentage buffs
        baseATK = int(baseATK + saFlatBuff) # Apply 'on attack' flat buffs
        
        ATKmultiplier = 0
        stack = False
        turnLimit = 0
        if (SAEffect.__contains__('aises ATK by') or
        SAEffect.__contains__('aises ATK & DEF by') and
        not (SAEffect.__contains__('Causes') and SAEffect.__contains__('and raises DEF'))):
            buff = SAEffect.split('aises ATK')[1]
            buff = buff.split(' by ')[1]
            buff = int(buff.split('%')[0])
            ATKmultiplier = ATKmultiplier + (buff/100)               
            if (not SAEffect.__contains__(f'aises ATK by {buff}% for 1 turn') and
            not SAEffect.__contains__(f'aises ATK & DEF by {buff}% for 1 turn')):
                stack = True
                if SAEffect.__contains__('temporarily'):
                    turnLimit = additional
                elif SAEffect.__contains__(' turns '):
                    turnLimit = SAEffect.split('% for ')[1]
                    turnLimit = int(turnLimit.split(' turns ')[0])
                else:
                    turnLimit = 11
        elif SAEffect.__contains__('raising ATK by'):
           buff = SAEffect.split(' by ')[1]
           buff = int(buff.split('%')[0])
           ATKmultiplier = ATKmultiplier + (buff/100)
        
        if (SAEffect.__contains__("; raises ") and
        (SAEffect.__contains__(" allies' ATK by ") or
        SAEffect.__contains__(" allies' ATK & DEF by ")) and
        not SAEffect.__contains__('(self excluded)')):
            buff = SAEffect.split("allies' ATK ")[1]
            buff = buff.split("by ")[1]
            buff = int(buff.split("%")[0])
            ATKmultiplier = ATKmultiplier + (buff/100)
            
        baseATKmultiplier = 0
        if (baseSAEffect.__contains__('Raises ATK by') or
        baseSAEffect.__contains__('Raises ATK & DEF by')):
           buff = baseSAEffect.split(' by ')[1]
           buff = int(buff.split('%')[0])
           baseATKmultiplier = baseATKmultiplier + (buff/100)
           #if (not baseSAEffect.__contains__(f'Raises ATK by {buff}% for 1 turn') and
           #not baseSAEffect.__contains__(f'Raises ATK & DEF by {buff}% for 1 turn')):
              #stack = True
              #if baseSAEffect.__contains__(' turns '):
                 #turnLimit = baseSAEffect.split('% for ')[1]
                 #turnLimit = int(turnLimit.split(' turns ')[0])
              #else:
                 #turnLimit = 11
        elif baseSAEffect.__contains__('raising ATK by'):
           buff = baseSAEffect.split(' by ')[1]
           buff = int(buff.split('%')[0])
           baseATKmultiplier = baseATKmultiplier + (buff/100)
        
        if (baseSAEffect.__contains__("; raises ") and
        (baseSAEffect.__contains__(" allies' ATK by ") or
        baseSAEffect.__contains__(" allies' ATK & DEF by ")) and
        not SAEffect.__contains__('(self excluded)')):
            buff = baseSAEffect.split("by ")[1]
            buff = int(buff.split("%")[0])
            baseATKmultiplier = baseATKmultiplier + (buff/100)
            
        SAmultiplier = 2.6 # Damage by default
        if (SAEffect.__contains__("low damage") or
        SAEffect.__contains__("Low damage")):
            SAmultiplier = 2.2
        elif (SAEffect.__contains__("huge damage") or
        SAEffect.__contains__("Huge damage") or
        SAEffect.__contains__("destructive damage") or
        SAEffect.__contains__("Destructive damage")):
            SAmultiplier = 2.9
        elif (SAEffect.__contains__("extreme damage") or
        SAEffect.__contains__("Extreme damage") or
        SAEffect.__contains__("mass damage") or
        SAEffect.__contains__("Mass damage")):
            SAmultiplier = 3.55
        elif (SAEffect.__contains__("supreme damage") or
        SAEffect.__contains__("Supreme damage")):
            if SAName.__contains__("(Extreme)"):
                SAmultiplier = 5.3
            else:
                SAmultiplier = 4.3
        elif (SAEffect.__contains__("immense damage")):
            if SAName.__contains__("(Extreme)"):
                SAmultiplier = 6.3
            else:
                SAmultiplier = 5.05
        elif (SAEffect.__contains__("mega-colossal damage")):
            if SAName.__contains__("(Extreme)"):
                SAmultiplier = 5.9
            else:
                SAmultiplier = 5.4
        elif (SAEffect.__contains__("colossal damage")):
            if SAName.__contains__("(Extreme)"):
                SAmultiplier = 4.2
            else:
                SAmultiplier = 3.95
                
        baseSAmultiplier = 2.6 # Damage by default for units with multiple SAs/early Ki SAs
        if (baseSAEffect.__contains__("low damage") or
        baseSAEffect.__contains__("Low damage")):
            baseSAmultiplier = 2.2
        elif (baseSAEffect.__contains__("huge damage") or
        baseSAEffect.__contains__("Huge damage") or
        baseSAEffect.__contains__("destructive damage") or
        baseSAEffect.__contains__("Destructive damage")):
            baseSAmultiplier = 2.9
        elif (baseSAEffect.__contains__("extreme damage") or
        baseSAEffect.__contains__("Extreme damage") or
        baseSAEffect.__contains__("mass damage") or
        baseSAEffect.__contains__("Mass damage")):
            baseSAmultiplier = 3.55
        elif (baseSAEffect.__contains__("supreme damage") or
        baseSAEffect.__contains__("Supreme damage")):
            if baseSAName.__contains__("(Extreme)"):
                baseSAmultiplier = 5.3
            else:
                baseSAmultiplier = 4.3
        elif (baseSAEffect.__contains__("immense damage")):
            if baseSAName.__contains__("(Extreme)"):
                baseSAmultiplier = 6.3
            else:
                baseSAmultiplier = 5.05
        elif (baseSAEffect.__contains__("mega-colossal damage")):
            if SAName.__contains__("(Extreme)"):
                baseSAmultiplier = 5.9
            else:
                baseSAmultiplier = 5.4
        elif (baseSAEffect.__contains__("colossal damage")):
            if SAName.__contains__("(Extreme)"):
                baseSAmultiplier = 4.2
            else:
                baseSAmultiplier = 3.95
            
        if (SAEffect.__contains__("(Super Attack power +") or
            SAEffect.__contains__("(Super Attack +")):
            SAPower = SAEffect.split("(Super Attack ")[1]
            SAPower = SAPower.split("+")[1]
            SAPower = (int(SAPower.split("%")[0]))/100
            SAmultiplier = SAmultiplier + SAPower
        elif (SAEffect.__contains__("Power will increase more if Super Attack level reaches")):
            SAmultiplier = SAmultiplier + .3
        
        if (baseSAEffect.__contains__("(Super Attack power +") or
            baseSAEffect.__contains__("(Super Attack +")):
            SAPower = SAEffect.split("(Super Attack ")[1]
            SAPower = SAPower.split("+")[1]
            SAPower = (int(SAPower.split("%")[0]))/100
            baseSAmultiplier = baseSAmultiplier + SAPower
        elif (baseSAEffect.__contains__("Power will increase more if Super Attack level reaches")):
            baseSAmultiplier = baseSAmultiplier + .3
            
        if (SAEffect.__contains__('critical hit') or
        baseSAEffect.__contains__('critical hit')):
            crit = True
        elif SAEffect.__contains__('attacks effective against all Types'):
            superEffective = True
                
        # Adds HiPo SA boost for SSR/UR/LR characters
        if stack:
         if rank == "SSR" or rank == "UR" or rank == "LR":
            print(f'Stacks ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier + 15 (.75%) HiPo SA Boost')
            SAmultiplier += .75
            baseSAmultiplier += .75
         else:
            print(f'Stacks ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier')
        else:
         if rank == "SSR" or rank == "UR" or rank == "LR":
               print(f'Raises ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier + 15 (.75%) HiPo SA Boost')
               SAmultiplier += .75
               baseSAmultiplier += .75
         else:
               print(f'Raises ATK by {ATKmultiplier*100}% with {SAmultiplier}% SA Multiplier')
        
        if counter != "":
            if counter.__contains__("enormous power"):
                counterPower = 2
            elif counter.__contains__("tremendous power"):
                counterPower = 3
            elif counter.__contains__("ferocious power"):
                counterPower = 4
        
        if SAEffect.__contains__("% chance of Super Attack transforming "):
            # Dev Note: Why do 'more power' and 'even more power' mean the same thing?
            # TBF this is just for the goten/trunks/marron F2P card's pre and post=eza
            # kit, respectively, but... yeah.
            transPower = .2
            if SAEffect.__contains__('transforming for greater power'):
                transPower = .6
            elif SAEffect.__contains__('Power will be supremely boosted for'):
                transPower = .9
                turnLimit = SAEffect.split('boosted for ')[1]
                turnLimit = int(turnLimit.split(' turns')[0])
                stack = True
            
            if turnLimit < 2:
                turnLimit = additional
                if rank == "SSR" or rank == "UR" or rank == "LR":
                    turnLimit = 2 + additional
            else:
                turnLimit = (math.ceil(turnLimit/2))*(additional+1)
            
            if stack or not additional == 0:
                if SAEffect.__contains__('Power will be supremely boosted for '):
                    for i in range(1, turnLimit):
                        if crit:
                            print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(transPower*i))))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(transPower*i))*1.9))})")
                        elif superEffective:
                            print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(transPower*i))))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(transPower*i))*1.5))})")
                        else:
                            print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+(transPower*i))))}")
                else:
                    for i in range(1, turnLimit):
                        if crit:
                            print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)*1.9))})")
                        elif superEffective:
                            print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)*1.5))})")
                        else:
                            print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)))}")
                for i in range(1, turnLimit):
                    if crit:
                        print(f"Normal Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.9))})")
                    elif superEffective:
                        print(f"Normal Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.5))})")
                    else:
                        print(f"Normal Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))}")
            else:
                if crit:
                    print(f"Transformed (20%) Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)))} (Crit: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)*1.9))})")
                    print(f"Normal Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier)))} (Crit: {str(int(ATK*(ATKmultiplier+SAmultiplier)*1.9))})")
                elif superEffective:
                    print(f"Transformed (20%) Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)))} (Super Effective: {str(int(ATK*(ATKmultiplier+SAmultiplier+.62)*1.5))})")
                    print(f"Normal Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier)))} (Super Effective: {str(int(ATK*(ATKmultiplier+SAmultiplier)*1.5))})")
                else:
                    print(f"Transformed (20%) Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)))}")
                    print(f"Normal Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier)))}")
        elif (SAEffect.__contains__("% chance of Super Attack transforming and ")):
            transPower = .2
            if SAEffect.__contains__('transforming and raises ATK '):
                ATKmultiplier = int(SAEffect[SAEffect.find(' by ')+4:SAEffect.find('% for')])/100
            elif SAEffect.__contains__('transforming for greater power'):
                transPower = .6
            elif SAEffect.__contains__('Power will be supremely boosted for '):
                transPower = .9
                turnLimit = SAEffect.split('boosted for ')[1]
                turnLimit = int(turnLimit.split(' turns')[0])
                stack = True
            
            if turnLimit < 2:
                turnLimit = additional
                if rank == "SSR" or rank == "UR" or rank == "LR":
                    turnLimit = 2 + additional
            else:
                turnLimit = (math.ceil(turnLimit/2))*(additional+1)
            
            if stack or not additional == 0:
                for i in range(1, turnLimit):
                    if crit:
                        print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)))} (Crit: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)*1.9))})")
                    elif superEffective:
                        print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)*1.5))})")
                    else:
                        print(f"Transformed ({int(transPower*100)}%) Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier+transPower)))}")
                
                if SAEffect.__contains__('transforming and raises ATK '):
                    ATKmultiplier = 0
                
                for i in range(1, turnLimit):
                    if crit:
                        print(f"Normal Super Attack APT ({str(i)} Stack): {str(int(ATK*(ATKmultiplier+SAmultiplier)))} (Crit: {str(int(ATK*(ATKmultiplier+SAmultiplier)*1.9))})")
                    elif superEffective:
                        print(f"Normal Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))} (Super Effective: {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)*1.5))})")
                    else:
                        print(f"Normal Super Attack APT ({str(i)} Stack): {str(int(ATK*((ATKmultiplier*i)+SAmultiplier)))}")
            else:
                if crit:
                    print(f"Transformed (20%) Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)))} (Crit: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)*1.9))})")
                    print(f"Normal Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier)))} (Crit: {str(int(ATK*(ATKmultiplier+SAmultiplier)*1.9))})")
                elif superEffective:
                    print(f"Transformed (20%) Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)))} (Super Effective: {str(int(ATK*(ATKmultiplier+SAmultiplier+.62)*1.5))})")
                    print(f"Normal Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier)))} (Super Effective: {str(int(ATK*(ATKmultiplier+SAmultiplier)*1.5))})")
                else:
                    print(f"Transformed (20%) Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier+.2)))}")
                    print(f"Normal Super Attack APT: {str(int(ATK*(ATKmultiplier+SAmultiplier)))}")
        elif stack:
            if SAEffect.__contains__('chance of raising ATK'):
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
                if rank == "SSR" or rank == "UR" or rank == "LR":
                    turnLimit = 2 + additional
            else:
                turnLimit = (math.ceil(turnLimit/2))*(additional+1)
            
            ATKmultiplier2 = ATKmultiplier
            mainStack = 0
            baseATKmultiplier2 = baseATKmultiplier
            baseStack = 0
            for i in range(1, turnLimit):
                if not baseKiValue == ki:
                    if i > 1 and math.ceil(((turnLimit - i) / (additional + 1)) % additional) == 0:
                        baseATKmultiplier2 += baseATKmultiplier
                        stackATK = int(baseATK*(baseATKmultiplier2+ATKmultiplier2+baseSAmultiplier))
                        baseStack += 1
                        
                        if crit:
                            print(f"Super Attack APT ({str(baseStack)} Stack, at {baseKiValue} Ki): {str(stackATK)} (Crit: {str(int(stackATK*1.9))})")
                        elif superEffective:
                            print(f"Super Attack APT ({str(baseStack)} Stack, at {baseKiValue} Ki): {str(stackATK)} (Super Effective: {str(int(stackATK*1.5))})")
                        else:
                            print(f"Super Attack APT ({str(baseStack)} Stack, at {baseKiValue} Ki): {str(stackATK)}")
                    else:
                        if mainStack != 0:
                            ATKmultiplier2 += ATKmultiplier
                        stackATK = int(baseATK*(baseATKmultiplier2+ATKmultiplier2+baseSAmultiplier))
                        mainStack += 1
                        
                        if crit:
                            print(f"Super Attack APT ({str(mainStack)} Stack, at {ki} Ki): {str(stackATK)} (Crit: {str(int(stackATK*1.9))})")
                        elif superEffective:
                            print(f"Super Attack APT ({str(mainStack)} Stack, at {ki} Ki): {str(stackATK)} (Super Effective: {str(int(stackATK*1.5))})")
                        else:
                            print(f"Super Attack APT ({str(mainStack)} Stack, at {ki} Ki): {str(stackATK)}")
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
            if SAEffect.__contains__('chance of raising ATK'):
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
                if rank == "SSR" or rank == "UR" or rank == "LR":
                    turnLimit = 2 + additional
            else:
                turnLimit = (math.ceil(turnLimit/2))*(additional+1)
            
            for i in range(1, turnLimit):
                if not baseKiValue == ki and i > 1:
                    stackATK = int(baseATK*((baseATKmultiplier*i)+ATKmultiplier+baseSAmultiplier))
                    
                    if crit:
                        print(f"Super Attack APT ({str(i)} Stack, at {baseKiValue} Ki): {str(stackATK)} (Crit: {str(int(stackATK*1.9))})")
                    elif superEffective:
                        print(f"Super Attack APT ({str(i)} Stack, at {baseKiValue} Ki): {str(stackATK)} (Super Effective: {str(int(stackATK*1.5))})")
                    else:
                        print(f"Super Attack APT ({str(i)} Stack, at {baseKiValue} Ki): {str(stackATK)}")
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
                        
        if counter != "":
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
        
        if active and active[1].__contains__('damage to '):
            if type(activeATK) != int:
                if type(activeATK[0]) == list:
                    activeATK[0] = activeATK[0][0]
            
            activeMultiplier = 550
            if active[1].__contains__('mega-colossal damage'):
                activeMultiplier = 440
            elif (active[1].__contains__('aises ATK by ') and
            active[1].__contains__('% temporarily then causes damage to enemy')):
                mult = active[1].split('aises ATK by ')[1]
                activeMultiplier = int(mult.split('% temp')[0])
                
            if active[1].__contains__('assively raises ATK temporarily'):
                activeMultiplier += 100
            elif active[1].__contains__('reatly raises ATK temporarily'):
                activeMultiplier += 50
            elif (active[1].__contains__('raises ATK by ') or
            active[1].__contains__("raises allies' ATK by ")):
                activeMultiplier += int((active[1].split('by ')[1]).split('%')[0])
            elif active[1].__contains__('aises ATK temporarily'):
                activeMultiplier += 30
            
            if type(activeATK) != int:
                activeATK = int(int(activeATK[0] * (1 + (int(activeATK[1]/100)))) + activeATK[2])
            if turnLimit > 1 and stack:
                for i in range (1, turnLimit):
                    stackATK = int(activeATK*((ATKmultiplier*i)+(activeMultiplier/100)))
                    if crit:
                        print(f'Active Skill APT ({i} Stack, {activeMultiplier}%): {stackATK} (Crit: {int(stackATK*1.9)})')
                    elif superEffective:
                        print(f'Active Skill APT ({i} Stack, {activeMultiplier}%): {stackATK} (Super Effective: {int(stackATK*1.5)})')
                    else:
                        print(f'Active Skill APT ({i} Stack, {activeMultiplier}%): {stackATK}')
            else:
                activeATK = int(activeATK*(activeMultiplier/100))
                if crit:
                    print(f'Active Skill APT ({activeMultiplier}%): {activeATK} (Crit: {int(activeATK*1.9)})')
                elif superEffective:
                    print(f'Active Skill APT ({activeMultiplier}%): {activeATK} (Super Effective: {int(activeATK*1.5)})')
                else:
                    print(f'Active Skill APT ({activeMultiplier}%): {activeATK}')
            
        print()

def calcATKCond(characterKit, condSoTATK, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil):
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
        if '%' not in buff:
            flat = True
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
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            
            cond1 = cond1.replace('When there is not ', 'When there is ')
            cond1 = cond1.replace('in the same turn are not', 'in the same turn are')
            cond1 = cond1.replace(' Ki Spheres not obtained', ' Ki Spheres obtained')
            cond1 = cond1.replace('When HP is not', 'When HP is')
            if flat:
                if "limit" in locals():
                    print(f"ATK {cond1}, with {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (int(limit) * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK {cond1}, with 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK {cond1}, with 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK {cond1}, with 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            else:
                if "limit" in locals():
                    print(f"ATK {cond1}, with {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (int(limit)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK {cond1}, with 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK {cond1}, with 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK {cond1}, with 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("For every Ki Sphere obtained, per "):
            category = condition.split(', per ')[1].replace(' (self excluded))', '')
            for i in range(0, 3):
                if flat:
                    print(f"ATK (With {i} {category}, 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {i} {category}, 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {i} {category}, 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK (With {i} {category}, 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {i} {category}, 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {i} {category}, 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff) * i), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("For every Ki Sphere obtained with "):
            kiStart = condition.split('obtained with ')[1]
            kiStart = int(kiStart.split(' or ')[0])
            print(f"ATK (With less than {kiStart} Ki Spheres Obtained):")
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK (With {3 + kiStart} Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {7.5 + kiStart} (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {23 - kiStart} (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + ((23 - kiStart) * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {kiStart + int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("For every Ki Sphere obtained"):
            cond2 = ''
            if condition.__contains__('when there is'):
                cond2 = 'When there is not' + (condition.split('when there is')[1])[:-1]
                print(f"ATK ({cond2}):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                cond2 = cond2.replace('When there is not', ', when there is')
            
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("For every Rainbow Ki Sphere obtained"):
            print("ATK (With 0 Rainbow Ki Spheres obtained):")
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) >= 2.5:
                        print(f"ATK (With 2.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (2.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 5:
                        print(f"ATK (With 5 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (2.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil) 
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) >= 2.5:
                        print(f"ATK (With 2.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (2.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 5:
                        print(f"ATK (With 5 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print("ATK (With 0 Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print("ATK (With 2.5 (AVG) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (2.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print("ATK (With 5 (Max) Rainbow Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("For every ") and condition.__contains__(" Ki Sphere obtained"):
            kiType = (condition.split('For every ')[1]).split(' Ki Sphere')[0]
            if flat:
                print(f"ATK (With 0 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                print(f"ATK (With 3 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                print(f"ATK (With 7.5 (AVG) {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                print(f"ATK (With 23 (Max) {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            else:
                print(f"ATK (With 0 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                print(f"ATK (With 3 {kiType} Ki Spheres Obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                print(f"ATK (With 7.5 (AVG) {kiType} Ki Spheres obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                print(f"ATK (With 23 (Max) {kiType} Ki Spheres obtained):")
                calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__(", per ") and condition.__contains__(" Ki Sphere obtained"):
            kiType = (condition.split('per ')[1]).split(' Ki Sphere')[0]
            condition = condition.split(', per')[0]
            if flat:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK (With 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK (With 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK (With 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (23 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + int(limit), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK (With {3 + kiStart} Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (3 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {7.5 + kiStart} (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (7.5 * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {23 - kiStart} (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + ((23 - kiStart) * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            else:
                if "limit" in locals():
                    if int(limit/int(buff)) > 3:
                        print(f"ATK {condition}, with 3 Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 7.5:
                        print(f"ATK {condition}, with 7.5 (AVG) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    if int(limit/int(buff)) >= 23:
                        print(f"ATK {condition}, with 23 (Max) Ki Spheres Obtained):")
                        calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With {int(limit/int(buff))} (Max) Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + int(limit), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    print(f"ATK (With 3 Ki Spheres Obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (3 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 7.5 (AVG) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (7.5 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    print(f"ATK (With 23 (Max) Ki Spheres obtained):")
                    calcATKCond(characterKit, copyCond, atkPerBuff + (23 * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("Starting from the ") and condition.__contains__(" turn "):
            turn = condition.split('Starting from the ')[1]
            print(f'ATK (Before the {turn}:')
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            
            print(f'ATK {condition}:')
            activeCondATK = [newPerBuff, newFlatBuff]
            calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif ((condition.__contains__("turn(s) from the character's entry turn") or
        condition.__contains__("turns from the character's entry turn")) and not
        condition.__contains__('On the ')):
            turn = (condition.split('For ')[1]).split(' turn')[0]
            activeCondATK = [newPerBuff, newFlatBuff]
            print(f"ATK {condition}:")
            calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            
            activeCondATK = [atkPerBuff, atkFlatBuff]
            print(f"ATK (After {turn} turn buff):")
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
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
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                    calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
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
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            else:
                for i in range(1, limitLoop):
                    if i == 1:
                        print(f'ATK (With {str(i)} {category} ally on the team):')
                    else:
                        print(f'ATK (With {str(i)} {category} allies on the team):')
                    if flat:
                        activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
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
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
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
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif (condition.__contains__("If the character's Ki is ")):
            activeCondATK = [newPerBuff, newFlatBuff]
            print(f"ATK {condition}:")
            calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)        
        elif (condition.__contains__("er existing enemy")):
            
            startLoop = 1
            limitLoop = 8
            if condition.__contains__('starting from the '):
                startLoop = condition.split('starting from the ')[1]
                startLoop = int((startLoop.split(' enemy')[0])[:-2])
                print(f'ATK (When facing less than {str(startLoop)} enemies):')
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)    
            
                for i in range(startLoop, limitLoop):
                    if i == 1:
                        print(f'ATK (When facing {str(i)} enemy):')
                    else:
                        print(f'ATK (When facing {str(i)} enemies):')
                        
                    if flat:
                        activeCondATK = [atkPerBuff, atkFlatBuff + ((i-1)*int(buff))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + ((i-1)*int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [atkPerBuff + ((i-1)*int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + ((i-1)*int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
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
                        calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i*int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [atkPerBuff + (i*int(buff)), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, atkPerBuff + (i*int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif (condition.__contains__("At the start of each turn")):
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1
            for i in range(1, limitLoop):
                activeCondATK = [atkPerBuff + (i*int(buff)), atkFlatBuff]
                print(f'ATK (Turn {str(i)}):')
                calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            if "limit" in locals():
                if limit % int(buff) != 0:
                    activeCondATK = [atkPerBuff + limit, atkFlatBuff]
                    print(f'ATK (Turn {str(i+1)}):')
                    calcATKCond(characterKit, copyCond, atkPerBuff + limit, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif (condition.__contains__("at the start of each turn")):
            # Test with TEQ HEP SSJ Vegeta, AGL WT Kid Gohan            
            condition = condition.replace('When HP is ', 'When HP is not ')
            print(f'ATK {condition.split(", ")[0]})')
            calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                
            condition = condition.replace('When HP is not', 'When HP is')
            condition = condition.replace(f", (up to {limit}%) at the start of each turn)", "")
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1
            for i in range(1, limitLoop):
                print(f'ATK {condition}, turn {str(i)}):')
                if flat:
                    activeCondATK = [atkPerBuff, atkFlatBuff + (i * int(buff))]
                    calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff + (i * int(buff)), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                else:
                    activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                    calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif (condition.__contains__("For every turn passed")):
            limitLoop = 8
            if "limit" in locals():
                limitLoop = int(limit/int(buff))+1

            for i in range(0, limitLoop):
                activeCondATK = [atkPerBuff + (i * int(buff)), atkFlatBuff]
                print(f'ATK ({str(i)} turns passed):')
                calcATKCond(characterKit, copyCond, atkPerBuff + (i * int(buff)), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("The more HP remaining"):
            for i in range(0, 101):
                if i % 10 == 0:
                    print("ATK at " + str(i) + "% HP:")
                    if flat:
                        activeCondATK = [atkPerBuff, int(atkFlatBuff + (int(buff)*(i/100)))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, int(atkFlatBuff + (int(buff)*(i/100))), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [int(atkPerBuff + (int(buff)*(i/100))), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, int(atkPerBuff + (int(buff)*(i/100))), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        elif condition.__contains__("The less HP remaining"):
            for i in range(0, 101):
                if i % 10 == 0:
                    print("ATK at " + str(i) + "% HP:")
                    if flat:
                        activeCondATK = [atkPerBuff, int(atkFlatBuff + (int(buff) - (int(buff)*(i/100))))]
                        calcATKCond(characterKit, copyCond, atkPerBuff, int(atkFlatBuff + (int(buff) - (int(buff)*(i/100)))), linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                    else:
                        activeCondATK = [int(atkPerBuff + (int(buff) - (int(buff)*(i/100)))), atkFlatBuff]
                        calcATKCond(characterKit, copyCond, int(atkPerBuff + (int(buff) - (int(buff)*(i/100)))), atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
        else:
            if condition.__contains__('self excluded'):
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
            else:
                activeCondATK = [newPerBuff, newFlatBuff]
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, newPerBuff, newFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
                
                condition = condition.replace(' is ', ' is not ')
                condition = condition.replace('As ', 'Not as ')
                condition = condition.replace('When facing ', 'When not facing ')
                condition = condition.replace(' are ', ' are not ')
                condition = condition.replace(' are not no', ' are')
                condition = condition.replace(' obtained', ' not obtained')
                condition = condition.replace(" has", " doesn't have")
                condition = condition.replace(", as the ", ", not as the ")
                condition = condition.replace("(For ", "(After ")
                condition = condition.replace("once only", "after one-time buff")
                condition = condition.replace('Great chance', 'Without RNG chance')
                
                if condition.__contains__('Activates the Entrance Animation'):
                    condition = "(Without Entrance buff)"
                
                activeCondATK = [atkPerBuff, atkFlatBuff]
                print(f"ATK {condition}:")
                calcATKCond(characterKit, copyCond, atkPerBuff, atkFlatBuff, linkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
    else:
        print(f'{characterKit.stats[1]} (Base ATK Stat)')
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
        ATK = int(characterKit.stats[1]*lead) # Apply leader skill
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
        
        if charUtil.domain:
            domainBuff = 0
            for line in charUtil.domain[1].split(';'):
                print(line)
                if line.__contains__(" allies' ATK "):
                    print(line)
                    buff = line.split('+')[1]
                    buff = int(buff.split('%')[0])
                    if characterKit.unitClass in line:
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
                    
            print(f'{int(ATK * (1 + (domainBuff/100)))} (With {domainBuff}% Domain Skill Buff: {charUtil.domain[0]})')
            calcActiveATK(active, int(ATK * (1 + (domainBuff/100))), activeATK, onAttackATK, crit, superEffective,
            characterKit.rank, characterKit.SANames, characterKit.SAEffects, characterKit.kiValues,
            characterKit.kiMultiplier, additional)
            print(f'{ATK} (Without Domain Skill Buff)')
        
        calcActiveATK(active, ATK, activeATK, onAttackATK, crit, superEffective,
        characterKit.rank, characterKit.SANames, characterKit.SAEffects, characterKit.kiValues,
        characterKit.kiMultiplier, additional)

def calculateDEF(condition, line, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, categories):
    if (condition.__contains__('The more HP remaining') or
    condition.__contains__('The less HP remaining')):
        buff = line.split('(up to ')[1]
        buff = buff.split(')')[0]
    else:
        buff = line.split('DEF ')[1]
    
    #print(condition)
    #print(line)
    #print(buff)
    secondEffect = ''
    if buff.__contains__('} '):
        secondEffect = ', ' + buff[buff.find('} ')+3:]
    if secondEffect.__contains__(') and chance of performing a critical hit'):
        secondEffect = secondEffect.split(') ')[0] + ', ' + secondEffect.split(') ')[2]
    condition += secondEffect.replace(' hen', ' when')
    
    if buff.__contains__('{passiveImg:down_r}'):
        buff = '-' + buff
    buff = buff.split('{passiveImg:')[0]
    
    flat = True
    if buff.__contains__('%'):
        flat = False
        buff = buff.split('%')[0]
    
    if condition.__contains__('Basic effect'):
        if (line.__contains__("hance of ") and line.__contains__(" DEF ")):
            RNG = line.split("hance of")[0]
            RNG = RNG.split("- ")[1]
            
            if flat:
                condSoTDEF.insertLine(f'DEF +{buff} ({RNG}hance)')
            else:
                condSoTDEF.insertLine(f'DEF +{buff}% ({RNG}hance)')
        elif (line.__contains__("- {passiveImg:once}")):
            if flat:
                condSoTDEF.insertLine(f'DEF +{buff} (Once only)')
            else:
                condSoTDEF.insertLine(f'DEF +{buff}% (Once only)')
        elif not line.__contains__('self excluded'):
            if line.__contains__('Category allies excluded'):
                category = line[line.find("} ('")+4:line.find("' Category")]
                if category not in categories:
                    if flat:
                        condSoTDEF.insertLine(f"DEF +{buff} ({condition})")
                    else:
                        condSoTDEF.insertLine(f"DEF +{buff}% ({condition})")
            else:
                if flat:
                    defFlatBuff += int(buff)
                else:
                    defPerBuff += int(buff)
    elif (condition.__contains__("When attacking") or
    condition.__contains__("when attacking") or secondEffect.__contains__("when attacking") or
    condition.__contains__("final blow") or
    condition.__contains__("receiving an attack") or
    condition.__contains__("evading an attack") or
    condition.__contains__("After guard is activated") or
    condition.__contains__("whenever guard is activated") or
    condition.__contains__("For every attack evaded") or
    condition.__contains__("For every attack performed") or
    condition.__contains__("For every Super Attack performed") or
    condition.__contains__("For every attack received") or
    (condition.__contains__("After performing ") and condition.__contains__("ttack(s) in battle")) or
    (condition.__contains__("After receiving ") and condition.__contains__("ttacks in battle")) or
    condition.__contains__("After performing a Super Attack") or
    condition.__contains__("When the target enemy is in the following status: ")):
        if flat:                
            onAttackDEF.insertLine(f"DEF +{buff} ({condition})")
        else:
            onAttackDEF.insertLine(f"DEF +{buff}% ({condition})")
    else:
        if condSoTDEF.searchLine(condition) != None:
            condSoTDEF.replaceLine(condition, buff)
        elif not line.__contains__('self excluded'):
            if flat:
                condSoTDEF.insertLine(f"DEF +{buff} ({condition})")
            else:
                condSoTDEF.insertLine(f"DEF +{buff}% ({condition})")
    return defPerBuff, defFlatBuff

def calculateATK(condition, line, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, categories):   
    if (condition.__contains__('The more HP remaining') or
    condition.__contains__('The less HP remaining')):
        buff = line.split('(up to ')[1]
        buff = buff.split(')')[0]
    else:
        buff = line.split('ATK ')[1]
        buff = buff.replace('& DEF ', '')
    buff = buff.replace(" and launches an additional attack", "")
    
    secondEffect = ''
    
    if line.__contains__(' chance of ATK'):
        secondEffect = (', ' + line[2:line.find(' of ')]).capitalize()
    condition += secondEffect.replace(' hen', ' when')
    
    if buff.__contains__('} ') and not (buff.__contains__('} and DEF')):
        secondEffect = ', ' + buff[buff.find('} ')+2:]
    if secondEffect.__contains__(') and chance of performing a critical hit'):
        secondEffect = secondEffect.split(') ')[0] + ', ' + secondEffect.split(') ')[2]
    condition += secondEffect.replace(' hen', ' when')
    
    if line.__contains__('- {passiveImg:once}'):
        condition += ", once only"
    
    if (buff.__contains__('{passiveImg:down_r}') and not
    buff.__contains__('{passiveImg:up_g} and DEF')):
        buff = '-' + buff
    buff = buff.split('{passiveImg:')[0]
    
    flat = True
    if buff.__contains__('%'):
        flat = False
        buff = buff.split('%')[0]
    
    if condition.__contains__('Basic effect'):
        if (line.__contains__("hance of ") and line.__contains__(" ATK ")):
            RNG = line.split("hance of")[0]
            RNG = RNG.split("- ")[1]
            
            if flat:
                condSoTATK.insertLine(f'ATK +{buff} ({RNG}hance)')
                #condSoTStat[f'{RNG}hance'][0] = buff
            else:
                condSoTATK.insertLine(f'ATK +{buff}% ({RNG}hance)')
                #condSoTStat[f'{RNG}hance'][0] = buff
                #condSoTStat[f'{RNG}hance'][2] = '%'
        elif (line.__contains__("- {passiveImg:once}")):
            if flat:
                condSoTATK.insertLine(f'ATK +{buff} (Once only)')
                #condSoTStat['Once only'][0] = buff
            else:
                condSoTATK.insertLine(f'ATK +{buff}% (Once only)')
                #condSoTStat['Once only'][0] = buff
                #condSoTStat['Once only'][2] = '%'
        elif not line.__contains__('self excluded'):
            if flat:
                atkFlatBuff += int(buff)
            else:
                atkPerBuff += int(buff)
    elif (condition.__contains__("When attacking") or
    condition.__contains__("when attacking") or secondEffect.__contains__("when attacking") or
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
    return atkPerBuff, atkFlatBuff

# Read through kit, sepearate lines based on activiation condition (SoT vs. 'on attack')
# Then, calculate SoT attack and conditional SoT attack  
def calculateMain(characterKit, atkLinkBuffs, defLinkBuffs, crit, active, charUtil):   
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
    
    if characterKit.rank == "SSR" or characterKit.rank == "UR" or characterKit.rank == "LR":
        additional += 1
    
    if (characterKit.passive).__contains__('critical hit'):
        crit = True
    elif (characterKit.passive).__contains__('Attacks are effective against all Types'):
        superEffective = True
    
    for line in (characterKit.passive).splitlines():
        if (((line.__contains__("Enemies'") or line.__contains__("enemies'") or
        line.__contains__("Enemy's") or (line.__contains__("enemy's") and
        not line.__contains__("evading enemy's attack") and
        not line.__contains__(" enemy's HP is"))) and
        not line.__contains__('allies') and
        not line.__contains__("enemy's Super Attack")) or
        (line.__contains__('Type allies') and not line.__contains__(characterKit.type)) or
        (line.__contains__('Class allies') and not line.__contains__(characterKit.unitClass)) or
        (line.__contains__("for allies whose names include ") and characterKit.name not in line)):
            continue
        
        if line.__contains__('and damage reduction rate '):
            line = line.replace(line[line.find('} and damage reduction rate'):line.find('} for')], '')
        if line.__contains__('& chance of performing a critical hit '):
            line = line.replace(' & chance of performing a critical hit', '')
            line = line.replace(', DEF ', ' & DEF ')
        elif line.__contains__('} and chance of performing a critical hit '):
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
            line = line.replace(line[line.find('} and '):line.find('hit ')+3], '}')
            if not line.__contains__('}'):
                line = '}' + line.split('}')[0]
        if (line.__contains__("} and ") and
        line.__contains__("chance of evading enemy's attack ")):
            line = line.replace(line[line.find('} and '):line.find('attack ')+6], '}')

        if line.__contains__("*"):
            condition = line[1:-1]
        
        if line.__contains__("allies' ") and line.__contains__('and if there is '):
            ally = line.split("allies' ")[0]
            cond1 = ('if there is ' + line.split(" and if there is ")[1])
            cond2 = cond1.split(", ")[1]
            cond2 = cond2.replace('plus an additional', ally + "allies'")
            cond1 = cond1[0:1].capitalize() + (cond1[1:].split(", ")[0])
            #condSoTStat[cond1] = {0, 0}
            
            if cond2.__contains__('ATK'):
                buff = (cond2.split('ATK ')[1]).replace('& DEF ', '')
                buff = buff.split('{passiveImg')[0]
                condSoTATK.insertLine(f'ATK +{buff} ({cond1})')
                #condSoTStat[cond1][0] = #condSoTStat[cond1][0] + buff
            if cond2.__contains__('DEF'):
                buff = cond2.split('DEF ')[1]
                buff = buff.split('{passiveImg')[0]
                condSoTDEF.insertLine(f'DEF +{buff} ({cond1})')
                #condSoTStat[cond1][1] = #condSoTStat[cond1][1] + buff
            
            line = line.split(" and if there is ")[0]
        elif line.__contains__("allies' ") and line.__contains__(', plus an additional '):
            ally = line.split("allies' ")[0]
            cond = line.split(', plus an additional')[1:]
            line = line.split(", plus an additional ")[0]
            
            for part in cond:
                if part.__contains__('for characters who also belong to the '):
                    if part.__contains__(' ATK & DEF '):
                        buff2 = part.split('DEF ')[1]
                        buff2 = int(buff2.split('%{')[0])
                        ally2 = part.split("for characters who also belong to the '")[1]
                        ally2 = ally2.split("' Category")[0]
                        
                        for category in characterKit.categories:
                            if category in ally2:
                                if flat:
                                    atkFlatBuff += buff2
                                    defFlatBuff += buff2
                                else:
                                    atkPerBuff += buff2
                                    defPerBuff += buff2
                    elif part.__contains__(' DEF'):
                        buff2 = part.split('DEF ')[1]
                        buff2 = int(buff2.split('%{')[0])
                        ally2 = part.split("for characters who also belong to the '")[1]
                        ally2 = ally2.split("' Category")[0]
                        
                        for category in characterKit.categories:
                            if category in ally2:
                                if flat:
                                    defFlatBuff += buff2
                                else:
                                    defPerBuff += buff2
                    elif part.__contains__('plus an additional ATK '):
                        buff2 = part.split('ATK ')[1]
                        buff2 = int(buff2.split('%{')[0])
                        ally2 = part.split("for characters who also belong to the '")[1]
                        ally2 = ally2.split("' Category")[0]
                        
                        for category in characterKit.categories:
                            if category in ally2:
                                if flat:
                                    atkFlatBuff += buff2
                                else:
                                    atkPerBuff += buff2
                elif line.__contains__('} and if '):
                    cond1 = f'{cond[0]} (When {line.split("and if ")[1]})'
                    
                    if cond1.__contains__('ATK'):
                        cond2 = cond1.replace('ATK ', "ATK +")
                        cond2 = cond2.replace('& DEF ', "")
                        condSoTATK.insertLine(cond2)
                    if cond1.__contains__('DEF'):
                        cond2 = cond1.replace('DEF ', "DEF +")
                        cond2 = cond2.replace('ATK & ', "")
                        condSoTDEF.insertLine(cond2)
                else:
                    part = ally + "allies'" + part
                    cond1 = '(When' + part.split(' when')[1] + ')'
                    cond2 = (part.split(' when')[0]).replace('{passiveImg:up_g}', '')
                    
                    cond3 = f'{cond2} {cond1}'
                    if cond2.__contains__('ATK'):
                        cond4 = cond3.replace('ATK ', "ATK +")
                        cond4 = cond4.replace('& DEF ', "")
                        condSoTATK.insertLine(cond4)
                    if cond2.__contains__('DEF'):
                        cond4 = cond3.replace('DEF ', "DEF +")
                        cond4 = cond4.replace('ATK & ', "")
                        condSoTDEF.insertLine(cond4)
            
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
        
        if ((line.__contains__('ATK ') or
        line.__contains__('ATK{passiveImg:')) and
        not line.__contains__('ATK Down')):
            atkPerBuff, atkFlatBuff = calculateATK(condition, line, atkPerBuff, atkFlatBuff, condSoTATK, onAttackATK, condSoTStat, onAttackStat, characterKit.categories)
            
        if ((line.__contains__('DEF ') or
        line.__contains__('DEF{passiveImg:')) and
        not line.__contains__('DEF Down')):
            defPerBuff, defFlatBuff = calculateDEF(condition, line, defPerBuff, defFlatBuff, condSoTDEF, onAttackDEF, condSoTStat, onAttackStat, characterKit.categories)

    activeCondATK = [atkPerBuff, atkFlatBuff]
    #print(condSoTStat)
    #print(onAttackStat)
    print(f"\nInitial percent buffs: {atkPerBuff}% ATK, {defPerBuff}% DEF")
    print(f"Initial flat buffs: {atkFlatBuff} ATK, {defFlatBuff} DEF\n")
    
    calcATKCond(characterKit, condSoTATK, atkPerBuff, atkFlatBuff, atkLinkBuffs, onAttackATK, crit, superEffective, additional, active, activeCondATK, charUtil)
    #input("Click any button to continue with unit defense:")
    #os.system('cls')
    #calcDEFCond(characterKit, condSoTDEF, defLinkBuffs, onAttackDEF, crit, superEffective, additional, 1)
    
# Read through kit, sepearate lines based on activiation condition (SoT vs. 'on attack')
# Then, calculate SoT defense and conditional SoT defense  
def calculateLinks(characterKit, partnerKit, charUtil):
    os.system('cls')
    print(f"Calculating: {characterKit.rank} {characterKit.type} {characterKit.name} (Linked with {partnerKit.rank} {partnerKit.type} {partnerKit.name}):")
    
    # Find all shared links
    sharedLinks = []
    i = 0
    if (characterKit.name != partnerKit.name or
    (int(partnerKit.id) >= 4000000 and characterKit.id != partnerKit.id)):
        print("\nShared Links:")
        for sharedLink in characterKit.links:
            if sharedLink in partnerKit.links:
                print(f"- {sharedLink} - {characterKit.linkBuffs[i]}")
                sharedLinks.append(characterKit.linkBuffs[i])
            i = i + 1
    else:
        print("Unit cannot link with partner (Shared name)")
        calculateMain(characterKit, 0, 0, False, characterKit.active, charUtil)
        return

    if not sharedLinks:
        print("Unit cannot link with partner (No shared links)")
        calculateMain(characterKit, 0, 0, False, characterKit.active, charUtil)
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
        atkLinkDebuffs = 0
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
        
        calculateMain(characterKit, atkLinkBuffs, defLinkBuffs, crit, characterKit.active, charUtil)
   
# Helper method to get all unit details
def getPartnerKit(partnerID):      
    partnerKit = []
    
    unitURL = f'https://dokkan.fyi/characters/{partnerID}'
    
    # Send a GET request to fetch the webpage content (Returns None if page fails)
    if (requests.get(unitURL)).status_code == 200:       
        response = (requests.get(unitURL)).text
    
        titleInfo = response[response.find('Details & link partners for DRAGON BALL Z Dokkan Battle character ')+66:response.find('. |')]
        
        # Search for EZA
        if response.__contains__('Super Extreme Z-Awakened '):
            titleInfo = titleInfo[titleInfo.find('Super Extreme Z-Awakened ')+25:]
        elif response.__contains__('Extreme Z-Awakened '):
            titleInfo = titleInfo[titleInfo.find('Extreme Z-Awakened ')+19:]
            
        os.system('cls')
        print('Retrieving unit information...')
        
        rank = titleInfo.split()[0]
        
        # Dev Note: No class information (Super/Extreme) listed for N/R/SR units
        # Using Hydros' site as temporary solution if N/R/SR unit is found
        if rank == 'UR' or rank == 'LR':
            type = titleInfo.split()[2]
        else:
            tempResponse = (requests.get(f'https://dokkanbattle.net/card/{partnerID}')).text
            type = titleInfo.split()[1]
        # Fix name (Not sure on case, units with mulitple words in name? (Nappa a (Giant Ape)))
        name = titleInfo[titleInfo.find(type)+4:]
        
        if partnerID >= 4000000:
            name += (' (<->)')
        
        if (partnerID == '1010640' or partnerID == '1010650' or 
        partnerID == '1010630' or partnerID == '1011041'):
            type = 'STR/INT'
                
        links = retrieveLinks(response)[0]
        
        # Create object containing all unit kit details
        characterKit = Partner(partnerID, type, rank, name, links)

        os.system('cls')
        return characterKit
    else:
        print('Failed to retrieve character information.')
        return None
    
# Helper method to get all unit details
def getKit(characterID):    
    characterKit = []
    
    originID = characterID
    if characterID % 2 == 0:
        characterID += 1
    
    unitURL = f'https://dokkan.fyi/characters/{originID}'
    
    # Send a GET request to fetch the webpage content (Returns None if page fails)
    if (requests.get(unitURL)).status_code == 200:       
        response = (requests.get(unitURL)).text
    
        titleInfo = response[response.find('Details & link partners for DRAGON BALL Z Dokkan Battle character ')+66:response.find('. |')]
        
        # Search for EZA
        EZA = 0
        if response.__contains__('Super Extreme Z-Awakened '):
            # SEZA selection
            EZA = int(input('Select option for EZA (0 - Base; 1 - EZA; 2 - SEZA): '))
            titleInfo = titleInfo[titleInfo.find('Super Extreme Z-Awakened ')+25:]
        elif response.__contains__('step&quot;:8') and characterID >= 4000000:
            # SEZA selection for Giant/Rage Form units
            EZA = int(input('Select option for EZA (0 - Base; 1 - EZA; 2 - SEZA): '))
            titleInfo = titleInfo[titleInfo.find('Extreme Z-Awakened ')+19:]
        elif response.__contains__('Extreme Z-Awakened '):
            # EZA selection
            EZA = int(input('Select option for EZA (0 - Base; 1 - EZA): '))
            titleInfo = titleInfo[titleInfo.find('Extreme Z-Awakened ')+19:]
            
        os.system('cls')
        print('Retrieving unit information...')
        
        rank = titleInfo.split()[0]
        
        # Dev Note: No class information (Super/Extreme) listed for N/R/SR units
        # Using Hydros' site as temporary solution if N/R/SR unit is found
        if rank == 'UR' or rank == 'LR':
            unitClass = titleInfo.split()[1]
            type = titleInfo.split()[2]
        elif rank == 'SSR':
            tempInfo = (requests.get(f'https://dokkan.fyi/characters/{characterID}')).text
            tempInfo = tempInfo[tempInfo.find('Details & link partners for DRAGON BALL Z Dokkan Battle character ')+66:tempInfo.find('. |')]
            unitClass = tempInfo.split()[1]
            type = tempInfo.split()[2]
        else:
            tempResponse = (requests.get(f'https://dokkanbattle.net/card/{characterID}')).text
            if tempResponse.__contains__('element EXTREME'):
                unitClass = 'Extreme'
            else:
                unitClass = 'Super'
            type = titleInfo.split()[1]
        name = titleInfo[titleInfo.find(type)+4:]
        
        if (originID == 1010640 or originID == 1010650 or 
        originID == 1010630 or originID == 1011041):
            type = 'STR/INT'
        
        transform = ''
        # Set ID of transformed card if detected
        if not response.__contains__('],&quot;transformation_character_id&quot;:null'):
            transform = response[response.find('],&quot;transformation_character_id&quot;:')+42:]
            transform = transform[:7]
        if characterID == 1015051:
            transform = [transform, '4015071', '4015071']
                
        title = response[response.find(name):response.find(f' | DOKKAN.FYI')]
        title = '[' + title[title.find(' - ')+3:] + ']'
        title = title.replace(title[title.find('" property'):], ']')
        lead = retrieveLead(response, rank, EZA)
        SANames, SAEffects, kiValues, kiMultiplier = retrieveSA(response, characterID, rank, EZA)
        passiveName, passive = retrievePassive(response, rank, EZA)
        links, linkBuffs = retrieveLinks(response)
        categories = retrieveCategories(response)
        
        # Dev Note: Why do WT Goten and Trunks have different wordings for practically the same passive?
        if characterID == 1024221:
            passive = passive.replace("- ATK & DEF 20%{passiveImg:up_g} and if there is another 'Bond of Friendship' Category ally attacking in the same turn, plus an additional ATK & DEF 5%{passiveImg:up_g}", '- ATK & DEF 20%{passiveImg:up_g}\n- An additional ATK & DEF 5%{passiveImg:up_g} when there is another "Bond of Friendship" Category ally attacking in the same turn')
        elif characterID == 1031051:
            passive = passive.replace('ATK100%', 'ATK 100%') # In-game parsing error for SSR SSJ3 Daima Vegeta
        elif characterID == 1013261:
            passive = passive.replace("- ATK & DEF 12%{passiveImg:up_g} and per 'Giant Form' Category ally on the team, plus an additional ATK & DEF 1%{passiveImg:up_g} (up to 3%)", "- ATK & DEF 12%{passiveImg:up_g}\n- An additional ATK & DEF 1%{passiveImg:up_g} per 'Giant Form' Category ally on the team (up to 3%)")
        elif characterID == 1013121:
            passive = passive.replace("- ATK & DEF 5%{passiveImg:down_y}", "- Super Class enemies' ATK & DEF 5%{passiveImg:down_y}")
        elif characterID == 1015891 and EZA == 0:
            passive = passive.replace(passive[passive.find(' and if there is a '):passive.find('3%{passiveImg:up_g}')], '\n- An additional ATK & DEF ')
            passive = passive.replace('3%{passiveImg:up_g}', '3%{passiveImg:up_g} when there is a "Vegeta' + "'" + 's Family" Category enemy')
        elif characterID == 1015901 and EZA == 0:
            passive = passive.replace(passive[passive.find(' and if there is a '):passive.find('3%{passiveImg:up_g}')], '\n- An additional ATK & DEF ')
            passive += ' when there is a "Goku' + "'" + 's Family" Category enemy'
        
        response = (requests.get(f'https://dokkan.fyi/characters/{characterID}')).text
        stats = retrieveStats(response, characterID, EZA, rank)
        
        domain = ''
        if response.__contains__('domain&quot;:{&quot;id&quot;:'):
            domain = response[response.find('domain&quot;:{&quot;id&quot;:'):]
            domainName = domain[domain.find(',&quot;name&quot;:&quot;')+24:domain.find('&quot;,&quot;description&quot;:&quot;')]
            domainEffect = domain[domain.find('&quot;,&quot;description&quot;:&quot;')+37:domain.find('&quot;}},')]
            domainEffect = domainEffect.replace('\\n', '')
            domainEffect = domainEffect.replace('&#39;', "'")
            domainEffect = domainEffect.replace('\\&quot;', "'")
            domainEffect = domainEffect.replace('&amp;', "&")
            domain = [domainName, domainEffect]
        
        active = ''
        if not response.__contains__('active_skill&quot;:null,'):
            active = response[response.find('active_skill&quot;:{&quot;id&quot;:'):]
            active = active.replace('&#39;', "'")
            active = active.replace('\\n', '')
            active = active.replace('&amp;', '&')
            active = active.replace('\\&quot;', "'")
            activeName = active[active.find(',&quot;name&quot;:&quot;')+24:active.find('&quot;,&quot;description&quot;:&quot;')]
            activeEffect = active[active.find('&quot;,&quot;description&quot;:&quot;')+37:active.find('&quot;,&quot;condition&quot;:&quot;')]
            activeCond = active[active.find('&quot;,&quot;condition&quot;:&quot;')+35:active.find('&quot;,&quot;effects&quot;:[')]
            
            # Adjust INT Kid Goku's Active multiplier for GBL (550% on JP, 650% on GBL)
            if characterID == 1016571:
                activeEffect = activeEffect.replace('Causes ', 'Massively raises ATK temporarily and causes ')
            active = [activeName, activeEffect, activeCond]
        
        if characterID >= 4000000:
            name += (' (<->)')
            
        stack = 0
        
        standby = ''
        if response.__contains__('finish_skills&quot;:[{'):
            standby = response[response.find('finish_skills&quot;:[{'):]
            standbyName = standby[standby.find('uot;name&quot;:&quot;')+21:standby.find('&quot;,&quot;description&quot;:&quot;')]
            standbyEffect = standby[standby.find('&quot;,&quot;description&quot;:&quot;')+37:standby.find('&quot;,&quot;condition&quot;:&quot;')]
            standbyEffect = standbyEffect.replace('\\n', '')
            standbyEffect = standbyEffect.replace('&#39;', "'")
            standbyCond = standby[standby.find('&quot;,&quot;condition&quot;:&quot;')+35:standby.find('&quot;,&quot;effects&quot;:[{')]
            standbyCond = standbyCond.replace('\\n', '')
            standbyCond = standbyCond.replace('&#39;', "'")
            standby = [standbyName, standbyEffect, standbyCond]
        
        # Create object containing all unit kit details
        characterKit = Unit(characterID, unitClass, type, rank, title, 
        name, lead, SANames, SAEffects, passiveName, passive, links, linkBuffs,
        categories, stats, kiValues, kiMultiplier, transform, active)
        
        # Create object containing all unit kit details
        charUtil = transformUtil(stack, standby, domain)

        os.system('cls')
        return characterKit, charUtil
    else:
        print('Failed to retrieve character information.')
        return None

# Method for implementing custom card concepts, EZAs, etc.
def readCardFile(fileName):
    with open(fileName, encoding="utf8") as file:
        # reading each line
        count = 1
        for line in file:
            match count:
                case 1:
                    line = line.split()
                    unitClass = line[0]
                    type = line[1]
                    rank = line[2]
                case 2:
                    title = '[' + line[:-1] + ']'
                case 3:
                    name = line[:-1]
                case 4:
                    lead = line[:-1]
                case 5:
                    # Dev Note: Adjust for multiple SAs
                    SANames = []
                    SANames.append(line[:-1])
                case 6:
                    # Dev Note: Adjust for multiple SAs
                    SAEffects = []
                    SAEffects.append(line[:-1])
                case 7:
                    passiveName = line[:-1]
                case 8:
                    line = line.replace('\\n', '\n')
                    passive = line[:-1]
                case 9:
                    links = []
                    link = ""
                    for word in line.split():
                        if word.__contains__(','):
                            link += word[:-1]
                            links.append(link)
                            link = ""
                        else:
                            link += word + " "
                    links.append(link[:-1])
                case 10:
                    linkBuffs = []
                    linkBuff = ""
                    for word in line.split():
                        if word.__contains__(','):
                            linkBuff += word[:-1]
                            linkBuffs.append(linkBuff)
                            linkBuff = ""
                        else:
                            linkBuff += word + " "
                    linkBuffs.append(linkBuff[:-1])
                case 11:
                    categories = []
                    category = ""
                    for word in line.split():
                        if word.__contains__(','):
                            category += word[:-1]
                            categories.append(category)
                            category = ""
                        else:
                            category += word + " "
                    categories.append(category[:-1])
                case 12:
                    stats = []
                    for word in line.split():
                        stats.append(int(word))
                case 13:
                    kiValues = []
                    kiValues.append(int(line[:-1]))
                case 14:
                    kiMultiplier = line[:-1]
                case 15:
                    index = 0
                    for word in line.split():
                        stats[index] = int(word)
                        index += 1
            count += 1
    
    # Create object containing all unit kit details
    characterKit = Unit(characterID, unitClass, type, rank, title, 
    name, lead, SANames, SAEffects, passiveName, passive, links, linkBuffs,
    categories, stats, kiValues, kiMultiplier, '')

    os.system('cls')
    return characterKit

def main(characterID, charUtil):
    if characterID == 0:        
        mainUnit = readCardFile(input('Add card .txt file here: '))
    else:
        mainUnit, charUtil = getKit(characterID)
    print(f'{mainUnit.unitClass} {mainUnit.type} {mainUnit.rank} {mainUnit.title} {mainUnit.name}')
    print(f'\nLeader Skill: {mainUnit.lead}')
    
    for SAName, SAEffect in zip(mainUnit.SANames, mainUnit.SAEffects):
        print(f'\nSuper Attack: {SAName} - {SAEffect}')
    
    print(f'\nPassive Skill: {mainUnit.passiveName}')
    print(mainUnit.passive)
    
    if charUtil.domain:
        print(f'\nDomain Skill: {charUtil.domain[0]}')
        print(f'- {charUtil.domain[1]}')
    
    if mainUnit.active:
        print(f'\nActive Skill: {mainUnit.active[0]}')
        print(f'- {mainUnit.active[1]}')
        print(f'- Condition: {mainUnit.active[2]}')
    
    print('\nLink Skills:')
    print(mainUnit.links)
    print(f'\nCategories:\n{mainUnit.categories}')
    
    if (mainUnit.rank == 'SSR' or mainUnit.rank == 'UR' or mainUnit.rank == 'LR'):
        print('\nMax Stats (100%): ')
    else:
        print('\nMax Stats: ')
        
    print(f'HP: {mainUnit.stats[0]} | ATK: {mainUnit.stats[1]} | DEF: {mainUnit.stats[2]}')
    
    if not mainUnit.links:
        input("No partners available. Click any button to continue: ")
        calculateLinks(mainUnit, mainUnit)
    else:
        partnerID = int(input("Enter the partner character's Card ID from Dokkan.FYI: "))
        partnerKit = getPartnerKit(partnerID)
        calculateLinks(mainUnit, partnerKit, charUtil)
    
    if mainUnit.transform != '':
        input("Click any button to continue with transformed form:")
        main(int(mainUnit.transform), charUtil)
    else:
        input("Click any button to finish the program:")
    
os.system('cls') # Clears terminal; replace with os.system('clear') if on Unix/Linux/Mac
print("Welcome to Manila's Dokkan Calculator (Powered by Dokkan.FYI by CapnMZ)")
characterID = int(input("Enter the tested character's Card ID from Dokkan.FYI: "))
charUtil = []
main(characterID, charUtil)