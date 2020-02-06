import pygame
import random
import math as notPygameMath
import random
from pygame import *

#colors, obviously
BLACK = (0,0,0)
WHITE = (255,255,255)
GRAY = (220,220,220)
#window dimensions
WIN_WIDTH = 800
WIN_HEIGHT = 576
MIN_NUM_ROWS = notPygameMath.ceil(WIN_HEIGHT / 32)
MIN_NUM_COLS = notPygameMath.ceil(WIN_WIDTH / 32)
#more window dimensions
HALF_WIDTH = int(WIN_WIDTH / 2)
HALF_HEIGHT = int(WIN_HEIGHT / 2)
DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
MAX_LEVELS = 8

# reads a .txt file and creates a dictionary of all the levels it found;
# the start of a level is denoted with a $ followed by the level name;
# the end of the level is denoted with an @ symbol;
def loadLevelFile(fileName):
    levels = dict()
    level = []
    with open(fileName, 'r') as file:
        lines = [line.rstrip('\n') for line in file]
    for line in lines:
        if line.startswith('$'):
            levelName = line[1:]
        elif line.startswith('@'):
            levels[levelName] = level
            level = []
        else:
            level.append(line)
    return levels

# saves in the same format as above; the key is the level name, and the
# level list is the value
def saveLevelFile(fileName, levelToSave, name):
    with open(fileName, 'w') as file:
        header = "$" + name + "\n"
        file.writelines(header)
        for line in levelToSave:
            line += "\n"
            file.writelines(line)
        file.writelines("@")
    file.close()

def playMusic():
    pygame.mixer.music.load("ambient_track.wav")
    pygame.mixer.music.play(loops = 100, start = 0.0)

def unHoverAll(buttons):
    for button in buttons:
        button.hoverOff()

def drawButtons(buttons, screen, outline=False):
    for button in buttons:
        if outline:
            pygame.draw.rect(screen, GRAY, (button.x, button.y, 32, 32), 4)
        image = transform.scale(button.image, (button.w, button.h))
        screen.blit(image, (button.x, button.y))
        if button.hover == True:
            pygame.draw.rect(screen, (200,200,200), (button.x, button.y, button.w, button.h), 1)

def drawQuitRestart(screen, myfont, player):
    label = myfont.render("Do you want to %s?" % (player.mode), 1, (255,255,255))
    label2 = myfont.render("Type Y or N", 1, (255,255,255))

    labelrect = label.get_rect()
    labelrect.centerx = screen.get_rect().centerx
    labelrect.centery = screen.get_rect().centery - 10

    labelrect2 = label2.get_rect()
    labelrect2.centerx = screen.get_rect().centerx
    labelrect2.centery = screen.get_rect().centery + 10

    screen.blit(label, labelrect)
    screen.blit(label2, labelrect2)

    pygame.draw.rect(screen, WHITE, (labelrect.centerx - 120, labelrect.centery - 20, 240, 60), 1)

# looks through the level (represented by a list), to generate the list of gameAssets' Platform objects;
# each block is different based on the surrounding blocks
def createLevelAndReturnPlayer(currLevel, spriteDict, gameAssets, platforms, enemies, nonCollideables,
                               toxicBubbles, inEditor):

    def getEdgeBlockType(edge):
        nonlocal currLevel, row, col, x, y, maxRow, maxCol, legalBlocks
        if edge == "left":
            if currLevel[row-1][1] == "P" and currLevel[row][1] == "P" and currLevel[row+1][1] == "P":
                return Platform(x, y, 9)
            if currLevel[row-1][1] != "P" and currLevel[row][1] == "P" and currLevel[row+1][1] == "P":
                return Platform(x, y, 10)
            if currLevel[row-1][1] == "P" and currLevel[row][1] == "P" and currLevel[row+1][1] != "P":
                return Platform(x, y, 12)
            if currLevel[row][1] != "P":
                return Platform(x, y, 4)
            return Platform(x, y, 9) #failsafe

        elif edge == "right":
            if currLevel[row-1][maxCol-1] == "P" and currLevel[row][maxCol-1] =="P" and currLevel[row+1][maxCol-1]=="P":
                return Platform(x, y, 9)
            if currLevel[row-1][maxCol-1] != "P" and currLevel[row][maxCol-1] =="P" and currLevel[row+1][maxCol-1]=="P":
                return Platform(x, y, 11)
            if currLevel[row-1][maxCol-1] == "P" and currLevel[row][maxCol-1] =="P" and currLevel[row+1][maxCol-1]!="P":
                return Platform(x, y, 13)
            if currLevel[row][maxCol-1] != "P":
                return Platform(x, y, 5)
            return Platform(x, y, 9) #failsafe

        elif edge == "top":
            if currLevel[1][col-1] == "P" and currLevel[1][col] == "P" and currLevel[1][col+1] == "P":
                return Platform(x, y, 9)
            if currLevel[1][col-1] != "P" and currLevel[1][col] == "P" and currLevel[1][col+1] == "P":
                return Platform(x, y, 13)
            if currLevel[1][col-1] == "P" and currLevel[1][col] == "P" and currLevel[1][col+1] != "P":
                return Platform(x, y, 12)
            if currLevel[1][col] != "P":
                return Platform(x, y, 8)
            return Platform(x, y, 9) #failsafe

        elif edge == "bot":
            if (currLevel[maxRow-1][col-1] in legalBlocks and currLevel[maxRow-1][col] in legalBlocks and
                currLevel[maxRow-1][col+1] in legalBlocks):
                return Platform(x, y, 9)
            if (currLevel[maxRow-1][col-1] not in legalBlocks and currLevel[maxRow-1][col] in legalBlocks and
                currLevel[maxRow-1][col+1] in legalBlocks):
                return Platform(x, y, 11)
            if (currLevel[maxRow-1][col-1] in legalBlocks and currLevel[maxRow-1][col] in legalBlocks and
                currLevel[maxRow-1][col+1] not in legalBlocks):
                return Platform(x, y, 10)
            if currLevel[maxRow-1][col] not in legalBlocks:
                return Platform(x, y, 1)
            return Platform(x, y, 9) #failsafe

    def getBlockType(type):
        nonlocal currLevel, row, col, x, y, maxRow, maxCol, legalBlocks
        # A number in the set of adjacent blocks means that there is a block there:
        #
        #   1 = upper left, 2 = upper middle, 3 = upper right
        #   4 = left side,                    5 = right side
        #   6 = lower left, 7 = lower middle, 8 = lower right
        #
        # The lack of a block will be represented by a single digit:
        #   e.g. 2 = no block above
        # The presence of another ground block will be represented by double digits:
        #   e.g. 44 = ground block to the left side of current block
        # The presence of a toxic pool block will be represented by triple digits:
        #   e.g. 555 = toxic pool to the right side of current block
        adjacentBlocks = set()
        # setting up adjacent blocks
        if type == "P" or type == "J":
            if currLevel[row-1][col-1] in legalBlocks:
                adjacentBlocks.add(11)
            else:
                adjacentBlocks.add(1)

            if currLevel[row-1][col] in legalBlocks:
                adjacentBlocks.add(22)
            else:
                adjacentBlocks.add(2)

            if currLevel[row-1][col+1] in legalBlocks:
                adjacentBlocks.add(33)
            else:
                adjacentBlocks.add(3)

            if currLevel[row][col-1] in legalBlocks:
                adjacentBlocks.add(44)
            else:
                adjacentBlocks.add(4)

            if currLevel[row][col+1] in legalBlocks:
                adjacentBlocks.add(55)
            else:
                adjacentBlocks.add(5)

            if currLevel[row+1][col-1] == "P":
                adjacentBlocks.add(66)
            else:
                adjacentBlocks.add(6)

            if currLevel[row+1][col] == "P":
                adjacentBlocks.add(77)
            else:
                adjacentBlocks.add(7)

            if currLevel[row+1][col+1] == "P":
                adjacentBlocks.add(88)
            else:
                adjacentBlocks.add(8)
            if type == "J":
                print(adjacentBlocks)

        elif type == "K":
            adjacentBlocks.add(1) 

            if currLevel[row-1][col] == "P":
                adjacentBlocks.add(22)
            elif currLevel[row-1][col] == "K":
                adjacentBlocks.add(222)
            else:
                adjacentBlocks.add(2)

            if currLevel[row-1][col+1] == "P":
                adjacentBlocks.add(33)
            elif currLevel[row-1][col+1] == "K":
                adjacentBlocks.add(333)
            else:
                adjacentBlocks.add(3)

            if currLevel[row][col-1] == "P":
                adjacentBlocks.add(44)
            elif currLevel[row][col-1] == "K":
                adjacentBlocks.add(444)
            else:
                adjacentBlocks.add(4)

            if currLevel[row][col+1] == "P":
                adjacentBlocks.add(55)
            elif currLevel[row][col+1] == "K":
                adjacentBlocks.add(555)
            else:
                adjacentBlocks.add(5)

            if currLevel[row+1][col-1] == "P":
                adjacentBlocks.add(66)
            elif currLevel[row+1][col-1] == "K":
                adjacentBlocks.add(666)
            else:
                adjacentBlocks.add(6)

            if currLevel[row+1][col] == "P":
                adjacentBlocks.add(77)
            elif currLevel[row+1][col] == "K":
                adjacentBlocks.add(777)
            else:
                adjacentBlocks.add(7)

            if currLevel[row+1][col+1] == "P":
                adjacentBlocks.add(88)
            elif currLevel[row+1][col+1] == "K":
                adjacentBlocks.add(888)
            else:
                adjacentBlocks.add(8)
        #finding out what type of block the adjacent blocks create
        if type == "P" or type == "J":
            if set([44,55,66,77,88, 2]).issubset(adjacentBlocks):
                return Platform(x, y, 1) #top
            if set([44,66,77, 2, 5]).issubset(adjacentBlocks):
                return Platform(x, y, 2) #upper right
            if set([55,77,88, 2, 4]).issubset(adjacentBlocks):
                if not inEditor:
                    return random.choice([Platform(x, y, 3), Platform(x, y, 3), Platform(x, y, 101)]) #upper left/mush
                else:
                    return Platform(x, y, 3)
            if set([11,22,44,66,77, 5]).issubset(adjacentBlocks):
                return Platform(x, y, 4) #right
            if set([22,33,55,77,88, 4]).issubset(adjacentBlocks):
                return Platform(x, y, 5) #left
            if set([11,22,44, 5, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 6) #lower right
            if set([22,33,55, 4, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 7) #lower left
            if set([11,22,33,44,55, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 8) #bot
            if set([11,22,33,44,55,66,77,88]).issubset(adjacentBlocks):
                if not inEditor:
                    num = random.randint(0,100)
                    if num < 12:
                        return Platform(x, y, 102) #inside alt 1
                    elif num < 15:
                        return Platform(x, y, 103) #inside alt 2
                return Platform(x, y, 9) #middle/inside
            if set([11,22,44,55,66,77,88]).issubset(adjacentBlocks):
                return Platform(x, y, 10) #inverted upper right
            if set([22,33,44,55,66,77,88]).issubset(adjacentBlocks):
                return Platform(x, y, 11) #inverted upper left
            if set([11,22,33,44,55,66,77]).issubset(adjacentBlocks):
                return Platform(x, y, 12) #inverted lower right
            if set([11,22,33,44,55,77,88]).issubset(adjacentBlocks):
                return Platform(x, y, 13) #inverted lower left
            if set([77, 2, 4, 5]).issubset(adjacentBlocks):
                return Platform(x, y, 14) #thin top
            if set([44, 2, 5, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 15) #thin right
            if set([55, 2, 4, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 16) #thin left
            if set([22, 4, 5, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 17) #thin bot
            if set([22,77, 4, 5]).issubset(adjacentBlocks):
                return Platform(x, y, 18) #thin up
            if set([44,55, 2, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 19) #thin side
            if set([22,44,66,77, 1, 5]).issubset(adjacentBlocks):
                return Platform(x, y, 20) #jut up 1
            if set([22,55,77,88, 3, 4]).issubset(adjacentBlocks):
                return Platform(x, y, 21) #jut up 2
            if set([11,22,44,55, 3, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 22) #jut right 1
            if set([44,55,66,77, 2, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 23) #jut right 2
            if set([22,33,55,77, 4, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 24) #jut down 1
            if set([11,22,44,77, 5, 6]).issubset(adjacentBlocks):
                return Platform(x, y, 25) #jut down 2
            if set([22,33,44,55, 1, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 26) #jut left 1
            if set([44,55,77,88, 2, 6]).issubset(adjacentBlocks):
                return Platform(x, y, 27) #jut left 2
            if set([22,44,55,66,77,88, 1, 3]).issubset(adjacentBlocks):
                return Platform(x, y, 28) #jut up
            if set([11,22,44,55,66,77, 3, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 29) #jut right
            if set([22,33,44,55,77,88, 1, 6]).issubset(adjacentBlocks):
                return Platform(x, y, 30) #jut left
            if set([11,22,33,44,55,77, 6, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 31) #jut down
            if set([22,44,55,66,77, 1, 3, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 32) #jut up right
            if set([22,44,55,77,88, 1, 3, 6]).issubset(adjacentBlocks):
                return Platform(x, y, 33) #jut up left
            if set([11,22,44,55,77, 3, 6, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 34) #jut down right
            if set([22,33,44,55,77, 1, 6, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 35) #jut down left
            if set([22,44,55,77, 1, 3, 6, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 36) #cross middle
            if set([11,22,44,55,77,88, 3, 6]).issubset(adjacentBlocks):
                return Platform(x, y, 37) #right diag
            if set([22,33,44,55,66,77, 1, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 38) #left diag
            if set([ 2, 4, 5, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 39) #single block
            if set([22,44,55, 1, 3, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 40) #thin jut up
            if set([22,55,77, 3, 4, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 41) #thin jut right
            if set([22,44,77, 1, 5, 6]).issubset(adjacentBlocks):
                return Platform(x, y, 42) #thin jut left
            if set([44,55,77, 2, 6, 8]).issubset(adjacentBlocks):
                return Platform(x, y, 43) #thin jut down
            if set([44,77, 2, 5]).issubset(adjacentBlocks):
                return Platform(x, y, 44) #thin upper right
            if set([55,77, 2, 4]).issubset(adjacentBlocks):
                return Platform(x, y, 45) #thin upper left
            if set([22,44, 5, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 46) #thin lower right
            if set([22,55, 4, 7]).issubset(adjacentBlocks):
                return Platform(x, y, 47) #thin lower left
        elif type == "K":
            if set([444,55,66,77,88, 2]).issubset(adjacentBlocks):
                return ToxicBlock(x, y, 48) #pool right corner
            if set([44,555,66,77,88, 2]).issubset(adjacentBlocks):
                return ToxicBlock(x, y, 49) #pool left corner
            if set([444,555,66,77,88, 2]).issubset(adjacentBlocks):
                return ToxicBlock(x, y, 50) #pool bot
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 51) #pool bot 2
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 52) #pool pit
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 53) #pool pit 2
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 54) #pool left
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 55) #pool left 2
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 56) #pool right
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 57) #pool right 2
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 58) #pool thin up
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 59) #pool thin up 2
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 60) #pool top
            if set([]).issubset(adjacentBlocks):
                return Platform(x, y, 61) #pool inside
        return Platform(x, y, 9)

    maxRow, maxCol = len(currLevel) - 1, len(currLevel[0]) - 1
    # legal blocks used for checking top row and block directly underneath
    # the block in those positions may be any of these legal blocks
    legalBlocks = ("P", "K", "S")
    player = None
    x = y = 0
    for row in range(len(currLevel)):
        for col in range(len(currLevel[row])):
            block = currLevel[row][col]
            if block == "I":
                d = PlatformInside(x, y)
                platforms.append(d)
                gameAssets.add(d)
            elif block == "U":
                u = PlatformInside2(x, y)
                platforms.append(u)
                gameAssets.add(u)
            elif block == "F":
                f = Fuel(x, y, spriteDict["fuel"])
                platforms.append(f)
                gameAssets.add(f)
            elif block == "E":
                e = ExitBlock(x, y)
                platforms.append(e)
                gameAssets.add(e)
            elif block == "S":
                s = Spike(x, y)
                platforms.append(s)
                gameAssets.add(s)
            elif block == "k":
                k = ToxicBubble(x, y)
                toxicBubbles.append(k)
                gameAssets.add(k)
            elif block == "H":
                h = Aid(x, y, spriteDict["aid"])
                platforms.append(h)
                gameAssets.add(h)
            elif block == "T":
                t = NonCollideable(x, y, "stone")
                nonCollideables.append(t)
                gameAssets.add(t)
            elif block == "G":
                g = NonCollideable(x, y, "grass")
                nonCollideables.append(g)
                gameAssets.add(g)
            elif block == "L":
                l = NonCollideable(x, y, "flower")
                nonCollideables.append(l)
                gameAssets.add(l)
            elif block == "M":
                m = NonCollideable(x, y, "mush")
                nonCollideables.append(m)
                gameAssets.add(m)
            elif block == "X":
                player = Player(x, y)
            elif block == "D":
                d = Enemy(x, y)
                enemies.append(d)
                gameAssets.add(d)
            elif block == "P" or block == "K" or block == "J":
                #check to make sure block is not on the outermost edge
                if col != 0 and col != maxCol and row != 0 and row != maxRow:
                    if block == "P":
                        p = getBlockType("P")
                    if block == "J":
                        p = getBlockType("J")
                    elif block == "K":
                        p = getBlockType("K")
                else:
                    #now for the outermost edge blocks
                    #the corners
                    if ((row,col) == (0,0) or (row,col) == (0, maxCol) or
                        (row,col) == (maxRow, 0) or (row,col) == (maxRow, maxCol)):
                        p = Platform(x, y, 9)
                    elif col == 0:
                        p = getEdgeBlockType("left")
                    elif col == maxCol:
                        p = getEdgeBlockType("right")
                    elif row == 0:
                        p = getEdgeBlockType("top")
                    elif row == maxRow:
                        p = getEdgeBlockType("bot")
                    else:
                        p = Platform(x, y, 9)
                platforms.append(p)
                gameAssets.add(p)

                if not inEditor:
                    num = random.randint(0,99)
                    if p.type in (1, 2, 3, 23, 27) and currLevel[row-1][col] not in ("H", "F", "E", "T", "G", "X", "S"):
                        if num < 6:
                            platforms.append(NonCollideable(x, y-32, "mush2"))
                            gameAssets.add(NonCollideable(x, y-32, "mush2"))
                        elif num < 8:
                            platforms.append(NonCollideable(x, y-32, "mush3"))
                            gameAssets.add(NonCollideable(x, y-32, "mush3"))
                        elif num < 14:
                            platforms.append(NonCollideable(x, y-32, "mush4"))
                            gameAssets.add(NonCollideable(x, y-32, "mush4"))
                        elif num < 18:
                            platforms.append(NonCollideable(x, y-32, "mush5"))
                            gameAssets.add(NonCollideable(x, y-32, "mush5"))
                        elif num < 20:
                            platforms.append(NonCollideable(x, y-32, "crystal"))
                            gameAssets.add(NonCollideable(x, y-32, "crystal"))
            x += 32
        y += 32
        x = 0
    return player

def main():
    pygame.init()
    pygame.mixer.init()
    level = 1
    play(level)

def play(level):
    pygame.init()
    pygame.mixer.init()

    '------------ Level Setup ------------'
    screen = pygame.display.set_mode(DISPLAY, 0, 32)
    screen.convert_alpha()
    pygame.display.set_caption("Lost Ship")
    fadeScreen = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
    fadeScreen.fill(BLACK)
    fsalpha = 0
    fsalpha2 = 255
    fadeScreen.set_alpha(fsalpha2)

    # myfont = pygame.font.SysFont("monospace", 15)
    myfont = pygame.font.SysFont("joystix", 15, bold=False, italic=False)

    timer = pygame.time.Clock()
    '------------ Custom Events ------------'
    #bleeding
    pygame.time.set_timer(pygame.USEREVENT, 1000)
    #flashlight dimming
    pygame.time.set_timer(pygame.USEREVENT + 1, 500)
    #animating drones
    pygame.time.set_timer(pygame.USEREVENT + 2, 500)
    #USEREVENT + 3 used for smoke puffs
    #animating toxic pools
    pygame.time.set_timer(pygame.USEREVENT + 4, 100)

    # 1 is on; -1 is off
    flashlight = 1

    keys = {'up':False, 'down':False, 'left':False, 'right':False}
    # bg = Surface((32,32))
    # bg.convert()
    # bg.fill(WHITE)
    "------------ Level Variations ------------"
    if type(level) == int:
        if level > MAX_LEVELS:
            main()
        if level in (1, 2, 3, 4, 8):
            flashlight = -1
    "------------ Loading Sprites ------------"
    spriteDict = dict()

    bg1 = pygame.image.load('bg.png')
    bg11 = pygame.image.load('bg11.png')
    bg12 = pygame.image.load('bg12.png')
    
    if level == 4:
        bg = bg11
    elif type(level) == int and level >= 5 and level != MAX_LEVELS:
        bg = bg12
    else:
        bg = bg1
    bgStone = pygame.image.load('stone_with_grass_2.png')

    stoneBlockTop = pygame.image.load('stone_block_top.png')
    stoneBlock = pygame.image.load('stone_block.png')
    stoneBlock2 = pygame.image.load('stone_block_2.png')

    alienGroundTop = pygame.image.load('alien_ground_1_top.png')
    alienGroundRightCorner = pygame.image.load('alien_ground_2_right.png')
    alienGroundLeftCorner = pygame.image.load('alien_ground_3_left.png')
    alienGroundRightSide = pygame.image.load('alien_ground_4_right_side.png')
    alienGroundLeftSide = pygame.image.load('alien_ground_5_left_side.png')
    alienGroundRightLower = pygame.image.load('alien_ground_6_right_lower.png')
    alienGroundLeftLower = pygame.image.load('alien_ground_7_left_lower.png')
    alienGroundBottom = pygame.image.load('alien_ground_8_bottom.png')
    alienGroundInside = pygame.image.load('alien_ground_9_inside.png')
    alienGroundInsideAlt = pygame.image.load('alien_ground_9_alt.png')
    alienGroundInsideAlt2 = pygame.image.load('alien_ground_9_alt_2.png')
    alienGroundInsideUpRight = pygame.image.load('alien_ground_10_inside_upper_right.png')
    alienGroundInsideUpLeft = pygame.image.load('alien_ground_11_inside_upper_left.png')
    alienGroundInsideLowRight = pygame.image.load('alien_ground_12_inside_lower_right.png')
    alienGroundInsideLowLeft = pygame.image.load('alien_ground_13_inside_lower_left.png')
    alienGroundThinTop = pygame.image.load('alien_ground_14.png')
    alienGroundThinRight = transform.rotate(alienGroundThinTop, 270)
    alienGroundThinLeft = transform.rotate(alienGroundThinTop, 90)
    alienGroundThinBottom = transform.rotate(alienGroundThinTop, 180)
    alienGroundThinUp = pygame.image.load('alien_ground_18.png')
    alienGroundThinSide = transform.rotate(alienGroundThinUp, 90)
    alienGroundJutUp1 = pygame.image.load('alien_ground_20.png')
    alienGroundJutUp2 = transform.flip(alienGroundJutUp1, True, False)
    alienGroundJutRight1 = transform.rotate(alienGroundJutUp1, 270)
    alienGroundJutRight2 = transform.flip(alienGroundJutRight1, False, True)
    alienGroundJutDown1 = transform.rotate(alienGroundJutUp1, 180)
    alienGroundJutDown2 = transform.flip(alienGroundJutDown1, True, False)
    alienGroundJutLeft1 = transform.rotate(alienGroundJutUp2, 90)
    alienGroundJutLeft2 = transform.flip(alienGroundJutLeft1, False, True)
    alienGroundJutUp = pygame.image.load('alien_ground_28.png')
    alienGroundJutRight = transform.rotate(alienGroundJutUp, 270)
    alienGroundJutLeft = transform.rotate(alienGroundJutUp, 90)
    alienGroundJutDown = transform.rotate(alienGroundJutUp, 180)
    alienGroundJutUpRight = pygame.image.load('alien_ground_32.png')
    alienGroundJutUpLeft = transform.rotate(alienGroundJutUpRight, 90)
    alienGroundJutDownRight = transform.rotate(alienGroundJutUpRight, 270)
    alienGroundJutDownLeft = transform.rotate(alienGroundJutUpRight, 180)
    alienGroundCrossMiddle = pygame.image.load('alien_ground_36.png')
    alienGroundRightDiag = pygame.image.load('alien_ground_37.png')
    alienGroundLeftDiag = transform.rotate(alienGroundRightDiag, 90)
    alienGroundSingle = pygame.image.load('alien_ground_39.png')
    alienGroundThinJutUp = pygame.image.load('alien_ground_40.png')
    alienGroundThinJutRight = transform.rotate(alienGroundThinJutUp, 270)
    alienGroundThinJutLeft = transform.rotate(alienGroundThinJutUp, 90)
    alienGroundThinJutDown = transform.rotate(alienGroundThinJutUp, 180)
    alienGroundThinUpperRight = pygame.image.load('alien_ground_44.png')
    alienGroundThinUpperLeft = transform.rotate(alienGroundThinUpperRight, 90)
    alienGroundThinLowerRight = transform.flip(alienGroundThinUpperRight, False, True)
    alienGroundThinLowerLeft = transform.rotate(alienGroundThinUpperRight, 180)

    toxicPoolRightCorner = pygame.image.load('alien_ground_48.png')
    toxicPoolLeftCorner = transform.flip(toxicPoolRightCorner, True, False)
    toxicPoolBottom = pygame.image.load('alien_ground_50.png')

    alienGroundRightPool = pygame.image.load('alien_ground_14_right_pool.png')
    alienGroundLeftPool = pygame.image.load('alien_ground_15_left_pool.png')

    mush = pygame.image.load('mush.png')
    mush2 = pygame.image.load('mush_2.png')
    mush3 = pygame.image.load('mush_3.png')
    mush4 = pygame.image.load('mush_4.png')
    mush5 = pygame.image.load('mush_5.png')
    crystal = pygame.image.load('crystal.png')

    floorSpike = pygame.image.load('spike.png')
    toxicBlock = pygame.image.load('toxic_block.png')
    grass = pygame.image.load('grass_1.png')
    flowers = pygame.image.load('grass_flower.png')
    splash = pygame.image.load('splash_art.png')
    splash2 = pygame.image.load('splash_art_2.png')
    pattern1 = pygame.image.load('wall_pattern.png')
    spriteDict["aid"] = pygame.image.load('aid.png')
    spriteDict["fuel"] = pygame.image.load('fuel.png')

    startButton = pygame.image.load('start_button.png')
    startButton2 = pygame.image.load('start_button_hoveron.png')
    startButtons = [startButton, startButton2]

    instructButton = pygame.image.load('instruct_button.png')
    instructButton2 = pygame.image.load('instruct_button_hoveron.png')
    instructButtons = [instructButton, instructButton2]

    creatorButton = pygame.image.load('creator_button.png')
    creatorButton2 = pygame.image.load('creator_button_hoveron.png')
    creatorButtons = [creatorButton, creatorButton2]

    backButton = pygame.image.load('back_button.png')
    backButton2 = pygame.image.load('back_button_hoveron.png')
    backButtons = [backButton, backButton2]

    nextButton = pygame.image.load('continue_button.png')
    nextButton2 = pygame.image.load('continue_button_hoveron.png')
    nextButtons = [nextButton, nextButton2]

    incRowButton = pygame.image.load('inc_button.png')
    decRowButton = transform.flip(incRowButton, True, False)
    incColButton = pygame.image.load('inc_button.png')
    decColButton = transform.flip(incColButton, True, False)

    trashCan = pygame.image.load('trash_can.png')
    saveButton = pygame.image.load('save_button.png')
    loadButton = pygame.image.load('load_button.png')

    iconBack = pygame.image.load('icon_back.png')
    testUserMadeLevel = pygame.image.load('user_level.png')
    exitBlock = pygame.image.load('exit_block.png')

    "------------ Add Alpha to Sprites ------------"
    grass.convert_alpha()
    flowers.convert_alpha()
    bgStone.convert_alpha()
    floorSpike.convert_alpha()
    toxicBlock.convert_alpha()

    stoneBlockTop.convert_alpha()
    stoneBlock.convert_alpha()
    stoneBlock2.convert_alpha()

    alienGroundTop.convert_alpha()
    alienGroundRightCorner.convert_alpha()
    alienGroundLeftCorner.convert_alpha()
    alienGroundInside.convert_alpha()

    pattern1.convert_alpha()

    startButton.convert_alpha()
    startButton2.convert_alpha()
    instructButton.convert_alpha()
    instructButton2.convert_alpha()
    bgRect = Bg(0,0)

    "------------ Initialize Game Object Group and Lists ------------"
    gameAssets = pygame.sprite.Group()

    joysticks = []
    for i in range(0, pygame.joystick.get_count()):
        joysticks.append(pygame.joystick.Joystick(i))
        joysticks[-1].init()
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    platforms = []
    nonCollideables = []
    enemies = []
    buttons = [] #main menu buttons
    creatorScreenButtons = [] #level editor setup buttons
    editorScreenButtons = [] #level editor buttons
    editorButtons = [] #buttons for the blocks in level editor
    harmfulBlocks = []
    toxicBubbles = []
    smokePuffs = []
    currentSmokePuff = 0

    if level == 1:
        drone = Enemy(300, 400)
        drone2 = Enemy(800, 200)
        drone3 = Enemy(900, 500)
        # gameAssets.add(drone, drone2, drone3)
        # enemies.append(drone)
        # enemies.append(drone2)
        # enemies.append(drone3)

    elif level == 2:
        drone = Enemy(200, 300)
        drone2 = Enemy(500, 400)
        drone3 = Enemy(900, 400)
        drone4 = Enemy(1400, 400)

    elif level == 3:
        boss = Boss(700, 300)
        gameAssets.add(boss)
        enemies.append(boss)

    "------------ Make Buttons ------------"
    # middle is 400
    start = MenuButton(300, 300, 200, 40, "play", startButtons)
    instructions = MenuButton(300, 340, 200, 40, "instructions", instructButtons)
    creator = MenuButton(300,380, 200, 40, "creator setup", creatorButtons)
    buttons.append(start)
    buttons.append(instructions)
    buttons.append(creator)

    # backgrounds are scaled down to 200 x 100 later, with a 50 gap on each side
    creatorBg1 = CreatorBgSelect(50, 100, 200, 100, bg1, bg1)
    creatorBg2 = CreatorBgSelect(300, 100, 200, 100, bg11, bg11)
    creatorBg3 = CreatorBgSelect(550, 100, 200, 100, bg12, bg12)
    incRow = RowColButton(WIN_WIDTH - 200, 400, 40, 40, incRowButton, "row", 1)
    decRow = RowColButton(WIN_WIDTH - 300, 400, 40, 40, decRowButton, "row", -1)
    incCol = RowColButton(WIN_WIDTH - 200, 450, 40, 40, incColButton, "col", 1)
    decCol = RowColButton(WIN_WIDTH - 300, 450, 40, 40, decColButton, "col", -1)
    back = MenuButton(40, 15, 200, 40, "menu", backButtons)
    nextScreen = MenuButton(WIN_WIDTH - 250, 15, 200, 40, "creator", nextButtons)

    creatorScreenButtons.append(creatorBg1)
    creatorScreenButtons.append(creatorBg2)
    creatorScreenButtons.append(creatorBg3)
    creatorScreenButtons.append(incRow)
    creatorScreenButtons.append(decRow)
    creatorScreenButtons.append(incCol)
    creatorScreenButtons.append(decCol)
    creatorScreenButtons.append(nextScreen)
    creatorScreenButtons.append(back)

    back2 = MenuButton(5, 5, 200, 40, "creator setup", backButtons)
    saveButton = SaveLoadButton(HALF_WIDTH - 40, 1,  30, 30, saveButton, "save")
    loadButton = SaveLoadButton(HALF_WIDTH + 10, 1,  30, 30, loadButton, "load")
    testUserLevel = TestUserLevel(550, 10, 200, 40, testUserMadeLevel)
    editorScreenButtons.append(back2)
    editorScreenButtons.append(saveButton)
    editorScreenButtons.append(loadButton)
    editorScreenButtons.append(testUserLevel)
    userIcon = pygame.image.load('user_icon.png')

    # "P" is the strEq, or string equivalent, that represents the block in a text file
    alienGroundBlock = transform.scale(alienGroundSingle, (30, 30))
    smallerExitBlock = transform.scale(exitBlock, (30, 30))
    deleteBlock = EditorBlock(193, WIN_HEIGHT-31, 30, 30, trashCan, " ")
    pblock = EditorBlock(226, WIN_HEIGHT-31, 30, 30, alienGroundBlock, "P")
    userBlock = EditorBlock(258, WIN_HEIGHT-31, 30, 30, userIcon, "X")
    eBlock = EditorBlock(290, WIN_HEIGHT-31, 30, 30, smallerExitBlock, "E")
    editorButtons.append(deleteBlock)
    editorButtons.append(pblock)
    editorButtons.append(userBlock)
    editorButtons.append(eBlock)

    # if player has not moved the mouse of pressed any buttons, then we have the start
    # button selected by default for the controller
    notMoved = True
    notMoved2 = True
    notMoved3 = True
    notMovedFade = True
    buttonSelected = 0

    "------------ Load and Create the Level ------------"
    # level is an int when you play through the main game mode
    if type(level) == int:
        # loads all the levels from levels.py
        allLevels = loadLevelFile('levels.txt')
        # loads the specific level
        currLevel = allLevels[str(level)]
    elif level == "userlevel":
        currentlySavedUserLevel = loadLevelFile('userLevels.txt')
        currLevel = currentlySavedUserLevel["userlevel1"]
    # loops through the list of strings that represents the level and add the objects
    # to their respective lists
    
    # when inEditor is true, the level creator will not randomly generate mushrooms,
    # otherwise when we are loading a new map, and not in the editor, we will generate those random
    # mushrooms for that extra special visual feel
    inEditor = False
    player = createLevelAndReturnPlayer(currLevel, spriteDict, gameAssets, platforms, enemies,
                                        nonCollideables, toxicBubbles, inEditor)
    if level == "userlevel":
        player.mode = "play"

    "------------ Object Initializations ------------"    
    # specific to the current level
    gameAssets.add(player)
    levelWidth  = len(currLevel[0])*32
    levelHeight = len(currLevel)*32
    view = Camera(makeCamera, levelWidth, levelHeight)
    editorCam = EditorCamera()
    blockHeld = BlockHeld()
    player2 = None #used for the level editor

    #plays background music
    # playMusic()

    if type(level) == int and level > 1:
        player.mode = "getNextLevel"
    playing = True

    '------------ Start the Game / Level ------------'
    while playing:
        if player.mode == "getNextLevel":
            label = myfont.render("Press space to continue . . .", 1, WHITE)
            screen.fill(BLACK)
            screen.blit(label, (10, WIN_HEIGHT - 40))
            pygame.display.update()

            for e in pygame.event.get():
                if e.type == KEYDOWN:
                    if e.key == K_SPACE:
                        player.mode = "play"
                if e.type == JOYBUTTONUP:
                    player.mode = "play"

        if player.mode == "menu":
            # first time in the menu, so we select start button by default
            if notMoved == True:
                unHoverAll(buttons)
                buttons[0].hoverOn()
                buttonSelected = 0
            notMoved2 = True #reset not moved for the level creator setup (since we are in the menu screen)
            notMoved3 = True #reset not moved for the level creator
            editorCam.reset()

            label = myfont.render("Your ship's auto pilot went off course and landed you here!", 1, WHITE)
            label2 = myfont.render("You are now lost on another planet with no way back.", 1, WHITE)
            label3 = myfont.render("Can you uncover the secret of this lost world and make it back home?", 1, WHITE)
            label4 = myfont.render("However, you are slowly running out of fuel . . .", 1, WHITE)
            label5 = myfont.render("At any time, you may press 'C' to exit the game.", 1, WHITE)
            label6 = myfont.render("     A 112 Term Project Game By Jiahao Zhou     ", 1, WHITE)
            screen.fill(BLACK)
            # buttons start at 300, 300 and are 200x100 pixels
            screen.blit(splash, (HALF_WIDTH-497,0))
            screen.blit(label, (140,150))
            screen.blit(label2, (170,170))
            screen.blit(label3, (110,190))
            screen.blit(label4, (185,210))
            screen.blit(label5, (190,230))
            screen.blit(label6, (190,250))

            # makes a wallpattern thing on the bottom
            # for y in range(10, WIN_HEIGHT // 30 - 3):
            # for x in range(WIN_WIDTH // 100):
            #     screen.blit(pattern1, (x * 100, WIN_HEIGHT - 40))

            for button in buttons:
                pygame.draw.rect(screen, (200,200,200), (button.x, button.y, button.w, button.h), 1)
            for e in pygame.event.get():
                "------------ Key Presses ------------"
                if e.type == KEYDOWN:
                    if e.key == K_s:
                        player.mode = "play"
                    if e.key == K_i:
                        player.mode = "instructions"
                    if e.key == K_e:
                        player.mode = "creator setup"
                    if e.key == K_0:
                        play(0)
                    if e.key == K_1:
                        play(1)
                    if e.key == K_2:
                        play(2)
                    if e.key == K_3:
                        play(3)
                    if e.key == K_4:
                        play(4)
                    if e.key == K_5:
                        play(5)
                    if e.key == K_6:
                        play(6)
                    if e.key == K_7:
                        play(7)
                    if e.key == K_8:
                        play(8)
                    if e.key == K_SPACE:
                        play(MAX_LEVELS - 1)
                    if e.key == K_c:
                        playing = False
                    if e.key == K_r:
                        main()
                "------------ Mouse Clicks ------------"
                if e.type == MOUSEBUTTONDOWN:
                    for button in buttons:
                        # print("button is", button, "e.pos is", e.pos)
                        if button.isInsideButton(e.pos):
                            # print("inside!")
                            button.clickedOn = True
                "------------ Mouse Releases ------------"
                if e.type == MOUSEBUTTONUP:
                    for button in buttons:
                        if button.isInsideButton(e.pos) and button.clickedOn == True:
                            button.executeTask(player)
                        button.clickedOn = False
                "------------ Mouse Movements ------------"
                if e.type == MOUSEMOTION:
                    for button in buttons:
                        if button.isInsideButton(e.pos):
                            unHoverAll(buttons)
                            button.hoverOn()
                            buttonSelected = buttons.index(button)
                            notMoved = False
                "------------ Controller Presses ------------"
                if e.type == JOYHATMOTION:
                    #first unhover any currently hovered button so that we can hover the new one
                    if e.value == (0,1): # D-pad up
                        buttonSelected -= 1
                        unHoverAll(buttons)
                    if e.value == (0,-1): # D-pad down
                        buttonSelected += 1
                        unHoverAll(buttons)
                    if buttonSelected > len(buttons) - 1:
                        buttonSelected = 0
                    if buttonSelected < 0:
                        buttonSelected = len(buttons) - 1
                    buttons[buttonSelected].hoverOn()
                    notMoved = False
                if e.type == JOYBUTTONUP and e.button == 0:
                        buttons[buttonSelected].executeTask(player)

            for button in buttons:
                screen.blit(button.image, (button.x, button.y))

            # only fades in once
            if notMovedFade == True:
                fadeScreen.fill(BLACK)
                if fsalpha2 > 230:
                    fsalpha2 -= 8
                if fsalpha2 > 180:
                    fsalpha2 -= 12
                if fsalpha2 <= 180:
                    fsalpha2 -= 15
                fadeScreen.set_alpha(fsalpha2)
                screen.blit(fadeScreen, (0,0))
                if fsalpha2 <= 30:
                    notMovedFade = False
                pygame.display.update()
            pygame.display.update()

        if player.mode == "instructions":
            label = myfont.render("Use the arrows keys to move around.", 1, WHITE)
            label2 = myfont.render("Avoid enemy drones and spikes.", 1, WHITE)
            label3 = myfont.render("Spikes will hurt you, but if you get caught by a drone you lose.", 1, WHITE)
            label4 = myfont.render("Find the exit to win.", 1, WHITE)
            label5 = myfont.render("To cheat, press 'F' to disable the darkness.", 1, WHITE)
            label6 = myfont.render("Additional keys:  R - Restart  C - Instant Quit  F - Toggle darkness", 1, WHITE)
            label7 = myfont.render("                  Q - Quit     P - Pause         P - Unpause (if paused)", 1, WHITE)
            label8 = myfont.render("Now press 'S' to start your adventure!", 1, WHITE)
            screen.blit(splash2, (HALF_WIDTH - 497, 0))
            screen.blit(label, (120,100))
            screen.blit(label2, (120,140))
            screen.blit(label3, (120,180))
            screen.blit(label4, (120,220))
            screen.blit(label5, (120,260))
            screen.blit(label6, (120,320))
            screen.blit(label7, (120,360))
            screen.blit(label8, (120,420))
            pygame.display.update()

            for e in pygame.event.get():
                if e.type == KEYDOWN and e.key == K_s:
                    player.mode = "play"
                if e.type == KEYDOWN and e.key == K_c:
                    playing = False
                if e.type == KEYDOWN and e.key == K_r:
                    main()
                if e.type == JOYBUTTONUP and e.button == 0:
                    player.mode = "play"

        if player.mode == "pause":
            label = myfont.render("                                PAUSED", 1, WHITE)
            label2 = myfont.render("        Press 'I' to view instructions again.", 1, WHITE)
            label3 = myfont.render("     Press 'P' or Triangle to resume playing.", 1, WHITE)
            label4 = myfont.render(" At any time, you may press 'C' to exit the game.", 1, WHITE)
            fadeScreen.blit(splash2, (HALF_WIDTH - 497, 0))
            fadeScreen.set_alpha(100)
            fadeScreen.blit(label, (200,200))
            fadeScreen.blit(label2, (200,250))
            fadeScreen.blit(label3, (200,300))
            fadeScreen.blit(label4, (200,350))
            screen.blit(fadeScreen, (0,0))
            pygame.display.update()

            for e in pygame.event.get():
                if e.type == KEYDOWN and e.key == K_p:
                    player.mode = "play"
                if e.type == KEYDOWN and e.key == K_i:
                    player.mode = "instructions"
                if e.type == KEYDOWN and e.key == K_c:
                    playing = False
                if e.type == JOYBUTTONDOWN and e.button == 3: #triangle
                    player.mode = "play"

        if player.mode == "play":
            timer.tick(60)
            for e in pygame.event.get():
                if e.type == QUIT:
                    pygame.quit()
                "------------ Key Presses ------------"
                if e.type == KEYDOWN:
                    if e.key == K_DOWN:
                        keys['down'] = True
                    if e.key == K_LEFT:
                        keys['left'] = True
                    if e.key == K_RIGHT:
                        keys['right'] = True
                    if e.key == K_UP:
                        if player.jumpsLeft > 0:
                            smoke = SmokePuff(player.rect.x + 8, player.rect.y + 10)
                            gameAssets.add(smoke)
                            smokePuffs += [smoke]
                            pygame.time.set_timer(pygame.USEREVENT + 3, 100)
                        player.jump()
                    if e.key == K_r:
                        player.mode = "restart"
                    if e.key == K_q:
                        player.mode = "quit"
                    if e.key == K_c:
                        pygame.quit()
                    if e.key == K_f:
                        flashlight *= -1
                    if e.key == K_t: # light never fades
                        if player.hacksOff == False:
                            player.hacksOff = True
                        else:
                            player.hacksOff = False
                        player.lightRadius = 400
                    if e.key == K_p:
                        player.mode = "pause"
                "------------ Custom Events ------------"
                if e.type == USEREVENT:
                    if player.bleeding:
                        player.lightG = 0
                        player.lightB = 0
                if e.type == USEREVENT + 1 and flashlight == 1 and player.hacksOff:
                    player.lightRadius -= 2
                if e.type == USEREVENT + 2:
                    for drone in enemies:
                        drone.update()
                if e.type == USEREVENT + 3:
                    for puff in smokePuffs:
                        puff.animate()
                if e.type == USEREVENT + 4:
                    for block in toxicBubbles:
                        block.animate()
                "------------ Key Releases ------------"
                if e.type == KEYUP:
                    if e.key == K_UP:
                        keys['up'] = False
                    if e.key == K_DOWN:
                        keys['down'] = False
                    if e.key == K_LEFT:
                        keys['left'] = False
                    if e.key == K_RIGHT:
                        keys['right'] = False
                "------------ Controller Presses ------------"
                if e.type == JOYHATMOTION:
                    if e.value == (1,0): # ps4 D-pad right
                        keys['right'] = True
                    elif e.value == (-1,0): # ps4 D-pad left
                        keys['left'] = True
                    elif e.value == (0,0):
                        keys['right'] = False
                        keys['left'] = False

                if e.type == JOYBUTTONDOWN:
                    if e.button == 0: # ps4 square
                        keys['down'] = True
                    if e.button == 1: # ps4 X
                        if player.jumpsLeft > 0:
                            smoke = SmokePuff(player.rect.x + 8, player.rect.y + 10)
                            gameAssets.add(smoke)
                            smokePuffs += [smoke]
                            pygame.time.set_timer(pygame.USEREVENT + 3, 100)
                        player.jump()
                    if e.button == 3: # ps4 triangle
                        player.mode = "pause"
                    if e.button == 6: # ps4 L2
                        flashlight *= -1
                    if e.button == 7: # ps4 R2
                        if player.hacksOff == False:
                            player.hacksOff = True
                        else:
                            player.hacksOff = False
                        player.lightRadius = 400


                if e.type == JOYBUTTONUP:
                    if e.button == 0: # square
                        keys['down'] = False
                    if e.button == 1: # X
                        keys['up'] = False
                    if e.button == 4: # L1
                        player.mode = "restart"
                    if e.button == 5: # R1
                        player.mode = "quit"

            "------------ Calculating flashlight x and y ------------"
            #calculating x
            if player.rect.x > levelWidth - HALF_WIDTH:
                x = player.rect.x - levelWidth + WIN_WIDTH + int(player.rect.w / 2)
            elif player.rect.x > HALF_WIDTH:
                x = HALF_WIDTH + int(player.rect.w / 2)
            else:
                x = player.rect.x + int(player.rect.w / 2)
            #calculating y
            if player.rect.y > levelHeight - HALF_HEIGHT:
                y = player.rect.y - levelHeight + WIN_HEIGHT + int(player.rect.h / 2)
            elif player.rect.y > HALF_HEIGHT:
                y = HALF_HEIGHT + int(player.rect.h / 2) - 5
            else:
                y = player.rect.y + int(player.rect.h / 2) - 5

            "------------ Drawing flashlight ------------"
            mask = pygame.surface.Surface((levelWidth, levelHeight)).convert_alpha()
            # 1 is on; -1 is off
            if flashlight == 1:
                alphaVal = 255
                delta = 5
                radius = player.lightRadius

                while radius > 143:
                    pygame.draw.circle(mask,(0,0,0,alphaVal), (x, y),radius)
                    alphaVal -= delta
                    radius -= delta
            else:
                pygame.draw.circle(mask,(0,0,0,0), (x,y), levelHeight * 2)
            #changes color back if it is red from bleeding
            if player.lightG < 150:
                player.lightG += 10
            if player.lightB < 130:
                player.lightB += 8
            # if True, this colors the flashlight with the player.light RGB values
            # otherwise, it's just the background
            if flashlight == 1 and False:
                screen.fill((player.lightR,player.lightG,player.lightB))

            view.update(player)
            screen.blit(bg, view.apply(bgRect))
            player.update(keys, platforms, enemies)

            #moving the drones
            for drone in enemies:
                # if player.nearEnemy(drone)
                drone.move(player, platforms, enemies, currLevel)

            "------------ Drawing gameAssets ------------"
            for e in gameAssets:
                if e == player.entityToRemove:
                    gameAssets.remove(e)
                else:
                    if isinstance(e, SmokePuff):
                        if e.stop == True:
                            gameAssets.remove(e)
                            smokePuffs.remove(e)
                    if isinstance(e, Enemy):
                        screen.blit(e.image, view.apply(e))
                    elif isinstance(e, NonCollideable):
                        if e.blockType == "grass":
                            screen.blit(grass, view.apply(e))
                        elif e.blockType == "flower":
                            screen.blit(flowers, view.apply(e))
                        elif e.blockType == "stone":
                            screen.blit(bgStone, view.apply(e))
                        elif e.blockType == "mush2":
                            screen.blit(mush2, view.apply(e))
                        elif e.blockType == "mush3":
                            screen.blit(mush3, view.apply(e))
                        elif e.blockType == "mush4":
                            screen.blit(mush4, view.apply(e))
                        elif e.blockType == "mush5":
                            screen.blit(mush5, view.apply(e))
                        elif e.blockType == "crystal":
                            screen.blit(crystal, view.apply(e))
                    else: # not NonCollideable
                        if isinstance(e, Platform):
                            if isinstance(e, ExitBlock):
                                screen.blit(e.image, view.apply(e))
                            elif True:
                                if e.type == None:
                                    screen.blit(alienGroundInside, view.apply(e))
                                elif e.type == 1:
                                    screen.blit(alienGroundTop, view.apply(e))
                                elif e.type == 2:
                                    screen.blit(alienGroundRightCorner, view.apply(e))
                                elif e.type == 3:
                                    screen.blit(alienGroundLeftCorner, view.apply(e))
                                elif e.type == 4:
                                    screen.blit(alienGroundRightSide, view.apply(e))
                                elif e.type == 5:
                                    screen.blit(alienGroundLeftSide, view.apply(e))
                                elif e.type == 6:
                                    screen.blit(alienGroundRightLower, view.apply(e))
                                elif e.type == 7:
                                    screen.blit(alienGroundLeftLower, view.apply(e))
                                elif e.type == 8:
                                    screen.blit(alienGroundBottom, view.apply(e))
                                elif e.type == 9:
                                    screen.blit(alienGroundInside, view.apply(e))
                                elif e.type == 10:
                                    screen.blit(alienGroundInsideUpRight, view.apply(e))
                                elif e.type == 11:
                                    screen.blit(alienGroundInsideUpLeft, view.apply(e))
                                elif e.type == 12:
                                    screen.blit(alienGroundInsideLowRight, view.apply(e))
                                elif e.type == 13:
                                    screen.blit(alienGroundInsideLowLeft, view.apply(e))
                                elif e.type == 14:
                                    screen.blit(alienGroundThinTop, view.apply(e))
                                elif e.type == 15:
                                    screen.blit(alienGroundThinRight, view.apply(e))
                                elif e.type == 16:
                                    screen.blit(alienGroundThinLeft, view.apply(e))
                                elif e.type == 17:
                                    screen.blit(alienGroundThinBottom, view.apply(e))
                                elif e.type == 18:
                                    screen.blit(alienGroundThinUp, view.apply(e))
                                elif e.type == 19:
                                    screen.blit(alienGroundThinSide, view.apply(e))
                                elif e.type == 20:
                                    screen.blit(alienGroundJutUp1, view.apply(e))
                                elif e.type == 21:
                                    screen.blit(alienGroundJutUp2, view.apply(e))
                                elif e.type == 22:
                                    screen.blit(alienGroundJutRight1, view.apply(e))
                                elif e.type == 23:
                                    screen.blit(alienGroundJutRight2, view.apply(e))
                                elif e.type == 24:
                                    screen.blit(alienGroundJutDown1, view.apply(e))
                                elif e.type == 25:
                                    screen.blit(alienGroundJutDown2, view.apply(e))
                                elif e.type == 26:
                                    screen.blit(alienGroundJutLeft1, view.apply(e))
                                elif e.type == 27:
                                    screen.blit(alienGroundJutLeft2, view.apply(e))
                                elif e.type == 28:
                                    screen.blit(alienGroundJutUp, view.apply(e))
                                elif e.type == 29:
                                    screen.blit(alienGroundJutRight, view.apply(e))
                                elif e.type == 30:
                                    screen.blit(alienGroundJutLeft, view.apply(e))
                                elif e.type == 31:
                                    screen.blit(alienGroundJutDown, view.apply(e))
                                elif e.type == 32:
                                    screen.blit(alienGroundJutUpRight, view.apply(e))
                                elif e.type == 33:
                                    screen.blit(alienGroundJutUpLeft, view.apply(e))
                                elif e.type == 34:
                                    screen.blit(alienGroundJutDownRight, view.apply(e))
                                elif e.type == 35:
                                    screen.blit(alienGroundJutDownLeft, view.apply(e))
                                elif e.type == 36:
                                    screen.blit(alienGroundCrossMiddle, view.apply(e))
                                elif e.type == 37:
                                    screen.blit(alienGroundRightDiag, view.apply(e))
                                elif e.type == 38:
                                    screen.blit(alienGroundLeftDiag, view.apply(e))
                                elif e.type == 39:
                                    screen.blit(alienGroundSingle, view.apply(e))
                                elif e.type == 40:
                                    screen.blit(alienGroundThinJutUp, view.apply(e))
                                elif e.type == 41:
                                    screen.blit(alienGroundThinJutRight, view.apply(e))
                                elif e.type == 42:
                                    screen.blit(alienGroundThinJutLeft, view.apply(e))
                                elif e.type == 43:
                                    screen.blit(alienGroundThinJutDown, view.apply(e))
                                elif e.type == 44:
                                    screen.blit(alienGroundThinUpperRight, view.apply(e))
                                elif e.type == 45:
                                    screen.blit(alienGroundThinUpperLeft, view.apply(e))
                                elif e.type == 46:
                                    screen.blit(alienGroundThinLowerRight, view.apply(e))
                                elif e.type == 47:
                                    screen.blit(alienGroundThinLowerLeft, view.apply(e))
                                elif e.type == 101:
                                    screen.blit(mush, view.apply(e))
                                elif e.type == 102:
                                    screen.blit(alienGroundInsideAlt, view.apply(e))
                                elif e.type == 103 and level in (4, 5, 6, 7):
                                    screen.blit(alienGroundInsideAlt2, view.apply(e))
                                else:
                                    screen.blit(alienGroundInside, view.apply(e))
                        elif isinstance(e, HarmfulBlock):
                            if isinstance(e, Spike):
                                screen.blit(floorSpike, view.apply(e))
                            elif isinstance(e, ToxicBlock):
                                if e.type == 48:
                                    screen.blit(toxicPoolRightCorner, view.apply(e))
                                elif e.type == 49:
                                    screen.blit(toxicPoolLeftCorner, view.apply(e))
                                elif e.type == 50:
                                    screen.blit(toxicPoolBottom, view.apply(e))
                        else:
                            screen.blit(e.image, view.apply(e))

            # transparent mask for the flashlight; 100% transparent if
            # the flashlight is not on (-1)
            screen.blit(mask, (0,0))

            "------------ Drawing HUD features ------------"
            health = "HEALTH: "
            for i in range(player.health):
                health += "■ "

            label = myfont.render(health, 1, (200,200,200))
            label2 = myfont.render("HACKS ON", 1, (250,10,10))
            screen.blit(label, (10, 10))
            pygame.draw.rect(screen, (200,200,200), (5, 5, 260, 25), 1)
            if player.hacksOff == False:
                screen.blit(label2, (WIN_WIDTH - 150, 10))

            if player.health == 0:
                player.mode = "game over"

            "------------ Level Creator / Editor Setup ------------"
        elif player.mode == "creator setup":
            # first time in the creator, so we select background 1 button by default
            if notMoved2 == True:
                unHoverAll(creatorScreenButtons)
                creatorScreenButtons[0].hoverOn()
                creatorScreenButtons[0].executeTask(player) # selects first pictures as the background selected
                buttonSelected = 0
            notMoved = True #not moved for the menu screen
            notMoved3 = True #not moved for the creator screen
            notMovedFade = True
            editorLevel = None #this will be an EditorLevel class object once we go into the creator screen
            editorCam.resetShifts()

            label = myfont.render("Level Creator", 1, WHITE)
            label2 = myfont.render("Background Selected", 1, WHITE)
            screen.fill(BLACK)
            screen.blit(splash2, (HALF_WIDTH - 497, 0))
            screen.blit(label, (HALF_WIDTH - 80, 28))
            screen.blit(label2, (HALF_WIDTH / 2 - 50, 380))

            for e in pygame.event.get():
                "------------ Mouse Clicks ------------"
                if e.type == MOUSEBUTTONDOWN:
                    for button in creatorScreenButtons:
                        if button.isInsideButton(e.pos):
                            button.clickedOn = True
                    # for button in editorButtons:
                "------------ Mouse Releases ------------"
                if e.type == MOUSEBUTTONUP:
                    for button in creatorScreenButtons:
                        if button.isInsideButton(e.pos) and button.clickedOn == True:
                            if isinstance(button, RowColButton):
                                button.executeTask(editorCam)
                            else:
                                button.executeTask(player)
                        button.clickedOn = False
                "------------ Mouse Movements ------------"
                if e.type == MOUSEMOTION:
                    for button in creatorScreenButtons:
                        if button.isInsideButton(e.pos):
                            unHoverAll(creatorScreenButtons)
                            button.hoverOn()
                            buttonSelected = creatorScreenButtons.index(button)
                            notMoved2 = False
                "------------ Controller Presses ------------"
                if e.type == JOYHATMOTION:
                    #first unhover any currently hovered button so that we can hover the new one
                    if e.value == (0,1): # D-pad up
                        buttonSelected -= 1
                        unHoverAll(creatorScreenButtons)
                    if e.value == (0,-1): # D-pad down
                        buttonSelected += 1
                        unHoverAll(creatorScreenButtons)
                    if buttonSelected > len(creatorScreenButtons) - 1:
                        buttonSelected = 0
                    if buttonSelected < 0:
                        buttonSelected = len(creatorScreenButtons) - 1
                    creatorScreenButtons[buttonSelected].hoverOn()
                    notMoved2 = False
                if e.type == JOYBUTTONUP and e.button == 0:
                    creatorScreenButtons[buttonSelected].executeTask(player)

            # draw the buttons
            drawButtons(creatorScreenButtons, screen)

            # draw the selected background screen
            if player.bgSelected != None:
                image = transform.scale(player.bgSelected, (200, 100))
                screen.blit(image, (150, 400))

            # draw the current number of rows and cols
            label = myfont.render("%d"  % (editorCam.rows), 1, WHITE)
            label2 = myfont.render("%d" % (editorCam.cols), 1, WHITE)
            screen.blit(label, (WIN_WIDTH - 240, 410))
            screen.blit(label2, (WIN_WIDTH - 240, 460))

            "------------ Level Creator / Editor ------------"
        elif player.mode == "creator":
            # first time in the creator, so we select button 1 by default
            if notMoved3 == True:
                unHoverAll(editorScreenButtons)
                editorScreenButtons[0].hoverOn()
                buttonSelected = 0
                grid = EditorGrid()

                if editorLevel == None:
                    editorLevel = EditorLevel(editorCam.rows, editorCam.cols)
            # print("[")
            # for row in editorLevel.board:
            #     print(row)
            # print("]")

            gridSurface = pygame.Surface([1000,1000], pygame.SRCALPHA, 32)
            gridSurface = gridSurface.convert_alpha()
            notMoved = True #not moved for the menu screen
            notMoved2 = True #not moved for the setup screen

            for e in pygame.event.get():
                "------------ Key Presses ------------"
                if e.type == KEYDOWN:
                    if e.key == K_UP:
                        keys['up'] = True
                    if e.key == K_DOWN:
                        keys['down'] = True
                    if e.key == K_LEFT:
                        keys['left'] = True
                    if e.key == K_RIGHT:
                        keys['right'] = True
                "------------ Key Releases ------------"
                if e.type == KEYUP:
                    if e.key == K_UP:
                        keys['up'] = False
                    if e.key == K_DOWN:
                        keys['down'] = False
                    if e.key == K_LEFT:
                        keys['left'] = False
                    if e.key == K_RIGHT:
                        keys['right'] = False
                "------------ Mouse Clicks ------------"
                if e.type == MOUSEBUTTONDOWN:
                    #if we click on a button, we do not want to draw behind the button
                    #at the same time
                    clickedAButton = False
                    #check if we clicked on save, load, back, etc.
                    for button in editorScreenButtons:
                        if button.isInsideButton(e.pos):
                            clickedAButton = True
                            if isinstance(button, SaveLoadButton):
                                # saving returns None, loading returns the loaded level
                                newLevel = button.executeTask(editorLevel.board)
                                if newLevel != None:
                                    editorLevel.board = newLevel
                                    editorCam.rows = len(newLevel)
                                    editorCam.cols = len(newLevel[0])
                            elif isinstance(button, TestUserLevel):
                                button.testLevel(editorLevel.board)
                            else:
                                button.clickedOn = True
                    #check if we clicked on one of the block types at the bottom
                    for button in editorButtons:
                        if button.isInsideButton(e.pos):
                            clickedAButton = True
                            blockHeld.hold(button)
                    #False when mouse button is released
                    editorLevel.mouseHeld = True
                    #if we have yet to select a block at the bottom
                    if blockHeld.selectedBlock != None and not clickedAButton:
                        editorLevel.addBlock(e.pos, blockHeld.strEq, editorCam)
                "------------ Mouse Releases ------------"
                if e.type == MOUSEBUTTONUP:
                    for button in editorScreenButtons:
                        if button.isInsideButton(e.pos) and button.clickedOn == True:
                            button.executeTask(player)
                        button.clickedOn = False
                    editorLevel.mouseHeld = False
                "------------ Mouse Movements ------------"
                if e.type == MOUSEMOTION:
                    for button in editorScreenButtons:
                        if button.isInsideButton(e.pos):
                            unHoverAll(editorScreenButtons)
                            button.hoverOn()
                            buttonSelected = editorScreenButtons.index(button)
                            notMoved3 = False
                    if editorLevel.mouseHeld == True and blockHeld.selectedBlock != None:
                        editorLevel.addBlock(e.pos, blockHeld.strEq, editorCam)
                "------------ Controller Presses ------------"
                if e.type == JOYHATMOTION:
                    #first unhover any currently hovered button so that we can hover the new one
                    if e.value == (0,1): # D-pad up
                        buttonSelected -= 1
                        unHoverAll(editorScreenButtons)
                    if e.value == (0,-1): # D-pad down
                        buttonSelected += 1
                        unHoverAll(editorScreenButtons)
                    if buttonSelected > len(editorScreenButtons) - 1:
                        buttonSelected = 0
                    if buttonSelected < 0:
                        buttonSelected = len(editorScreenButtons) - 1
                    editorScreenButtons[buttonSelected].hoverOn()
                    notMoved3 = False
                if e.type == JOYBUTTONUP and e.button == 0:
                    editorScreenButtons[buttonSelected].executeTask(player)

            #reset stuff
            gameAssets = pygame.sprite.Group()

            platforms = []
            nonCollideables = []
            enemies = []
            # buttons = [] #main menu buttons
            # creatorScreenButtons = [] #level editor setup buttons
            # editorScreenButtons = [] #level editor buttons
            # editorButtons = [] #buttons for the blocks in level editor
            harmfulBlocks = []
            toxicBubbles = []
            # check to see if user pressed any arrow keys, if so, we will update the new x and y shifts
            # that will shift all the blocks in the level editor too
            
            #see note above during level creation about inEditor
            inEditor = True
            player2 = createLevelAndReturnPlayer(editorLevel.board, spriteDict, gameAssets, platforms, enemies,
                                        nonCollideables, toxicBubbles, inEditor)

            editorCam.update(keys, gameAssets, player2)

            if player2 != None:
                for e in gameAssets:
                    if isinstance(e, Player):
                        gameAssets.remove(e)
                gameAssets.add(player2)

            #set the background to whatever was selected on the setup screen
            screen.blit(player.bgSelected, (editorCam.xshifted * 32, editorCam.yshifted * 32))

            for e in gameAssets:
                if e == player.entityToRemove:
                    gameAssets.remove(e)
                else:
                    if isinstance(e, SmokePuff):
                        if e.stop == True:
                            gameAssets.remove(e)
                            smokePuffs.remove(e)
                    if isinstance(e, Enemy):
                        screen.blit(e.image, (e.x, e.y))
                    elif isinstance(e, NonCollideable):
                        if e.blockType == "grass":
                            screen.blit(grass, (e.x, e.y))
                        elif e.blockType == "flower":
                            screen.blit(flowers, (e.x, e.y))
                        elif e.blockType == "stone":
                            screen.blit(bgStone, (e.x, e.y))
                        elif e.blockType == "mush2":
                            screen.blit(mush2, (e.x, e.y))
                        elif e.blockType == "mush3":
                            screen.blit(mush3, (e.x, e.y))
                        elif e.blockType == "mush4":
                            screen.blit(mush4, (e.x, e.y))
                        elif e.blockType == "crystal":
                            screen.blit(crystal, (e.x, e.y))
                    else: # not NonCollideable
                        if isinstance(e, Platform):
                            if isinstance(e, ExitBlock):
                                screen.blit(e.image, (e.x, e.y))
                            elif True:
                                if e.type == None:
                                    screen.blit(alienGroundInside, (e.x, e.y))
                                elif e.type == 1:
                                    screen.blit(alienGroundTop, (e.x, e.y))
                                elif e.type == 2:
                                    screen.blit(alienGroundRightCorner, (e.x, e.y))
                                elif e.type == 3:
                                    screen.blit(alienGroundLeftCorner, (e.x, e.y))
                                elif e.type == 4:
                                    screen.blit(alienGroundRightSide, (e.x, e.y))
                                elif e.type == 5:
                                    screen.blit(alienGroundLeftSide, (e.x, e.y))
                                elif e.type == 6:
                                    screen.blit(alienGroundRightLower, (e.x, e.y))
                                elif e.type == 7:
                                    screen.blit(alienGroundLeftLower, (e.x, e.y))
                                elif e.type == 8:
                                    screen.blit(alienGroundBottom, (e.x, e.y))
                                elif e.type == 9:
                                    screen.blit(alienGroundInside, (e.x, e.y))
                                elif e.type == 10:
                                    screen.blit(alienGroundInsideUpRight, (e.x, e.y))
                                elif e.type == 11:
                                    screen.blit(alienGroundInsideUpLeft, (e.x, e.y))
                                elif e.type == 12:
                                    screen.blit(alienGroundInsideLowRight, (e.x, e.y))
                                elif e.type == 13:
                                    screen.blit(alienGroundInsideLowLeft, (e.x, e.y))
                                elif e.type == 14:
                                    screen.blit(alienGroundThinTop, (e.x, e.y))
                                elif e.type == 15:
                                    screen.blit(alienGroundThinRight, (e.x, e.y))
                                elif e.type == 16:
                                    screen.blit(alienGroundThinLeft, (e.x, e.y))
                                elif e.type == 17:
                                    screen.blit(alienGroundThinBottom, (e.x, e.y))
                                elif e.type == 18:
                                    screen.blit(alienGroundThinUp, (e.x, e.y))
                                elif e.type == 19:
                                    screen.blit(alienGroundThinSide, (e.x, e.y))
                                elif e.type == 20:
                                    screen.blit(alienGroundJutUp1, (e.x, e.y))
                                elif e.type == 21:
                                    screen.blit(alienGroundJutUp2, (e.x, e.y))
                                elif e.type == 22:
                                    screen.blit(alienGroundJutRight1, (e.x, e.y))
                                elif e.type == 23:
                                    screen.blit(alienGroundJutRight2, (e.x, e.y))
                                elif e.type == 24:
                                    screen.blit(alienGroundJutDown1, (e.x, e.y))
                                elif e.type == 25:
                                    screen.blit(alienGroundJutDown2, (e.x, e.y))
                                elif e.type == 26:
                                    screen.blit(alienGroundJutLeft1, (e.x, e.y))
                                elif e.type == 27:
                                    screen.blit(alienGroundJutLeft2, (e.x, e.y))
                                elif e.type == 28:
                                    screen.blit(alienGroundJutUp, (e.x, e.y))
                                elif e.type == 29:
                                    screen.blit(alienGroundJutRight, (e.x, e.y))
                                elif e.type == 30:
                                    screen.blit(alienGroundJutLeft, (e.x, e.y))
                                elif e.type == 31:
                                    screen.blit(alienGroundJutDown, (e.x, e.y))
                                elif e.type == 32:
                                    screen.blit(alienGroundJutUpRight, (e.x, e.y))
                                elif e.type == 33:
                                    screen.blit(alienGroundJutUpLeft, (e.x, e.y))
                                elif e.type == 34:
                                    screen.blit(alienGroundJutDownRight, (e.x, e.y))
                                elif e.type == 35:
                                    screen.blit(alienGroundJutDownLeft, (e.x, e.y))
                                elif e.type == 36:
                                    screen.blit(alienGroundCrossMiddle, (e.x, e.y))
                                elif e.type == 37:
                                    screen.blit(alienGroundRightDiag, (e.x, e.y))
                                elif e.type == 38:
                                    screen.blit(alienGroundLeftDiag, (e.x, e.y))
                                elif e.type == 39:
                                    screen.blit(alienGroundSingle, (e.x, e.y))
                                elif e.type == 40:
                                    screen.blit(alienGroundThinJutUp, (e.x, e.y))
                                elif e.type == 41:
                                    screen.blit(alienGroundThinJutRight, (e.x, e.y))
                                elif e.type == 42:
                                    screen.blit(alienGroundThinJutLeft, (e.x, e.y))
                                elif e.type == 43:
                                    screen.blit(alienGroundThinJutDown, (e.x, e.y))
                                elif e.type == 44:
                                    screen.blit(alienGroundThinUpperRight, (e.x, e.y))
                                elif e.type == 45:
                                    screen.blit(alienGroundThinUpperLeft, (e.x, e.y))
                                elif e.type == 46:
                                    screen.blit(alienGroundThinLowerRight, (e.x, e.y))
                                elif e.type == 47:
                                    screen.blit(alienGroundThinLowerLeft, (e.x, e.y))
                                elif e.type == 101:
                                    screen.blit(mush, (e.x, e.y))
                                elif e.type == 102:
                                    screen.blit(alienGroundInsideAlt, (e.x, e.y))
                        elif isinstance(e, HarmfulBlock):
                            if isinstance(e, Spike):
                                screen.blit(floorSpike, (e.x, e.y))
                            elif isinstance(e, ToxicBlock):
                                if e.type == 48:
                                    screen.blit(toxicPoolRightCorner, (e.x, e.y))
                                elif e.type == 49:
                                    screen.blit(toxicPoolLeftCorner, (e.x, e.y))
                                elif e.type == 50:
                                    screen.blit(toxicPoolBottom, (e.x, e.y))
                        else:
                            screen.blit(e.image, (e.x, e.y))

            #draws the block selected text
            label = myfont.render("BLOCK SELECTED", 1, (WHITE))
            screen.blit(label, (5, WIN_HEIGHT - 32))

            pygame.draw.rect(screen, (150,33,88), (160, WIN_HEIGHT-31, 32, 32), 8)
            if blockHeld.selectedBlock != None:
                screen.blit(blockHeld.selectedBlock, (161,WIN_HEIGHT-31))
            grid.update(gridSurface)
            screen.blit(gridSurface, (-32,-32))
            drawButtons(editorScreenButtons, screen)
            outline = True
            drawButtons(editorButtons, screen, outline)

        elif player.mode == "quit" or player.mode == "restart":
            drawQuitRestart(screen, myfont, player)

            for e in pygame.event.get():
                if e.type == KEYDOWN:
                    # yes
                    if e.key == K_y:
                        if player.mode == "quit":
                            playing = False
                        elif player.mode == "restart":
                            main()
                    # no
                    elif e.key == K_n:
                        if player.mode == "quit" or player.mode == "restart":
                            player.mode = "play"

                if e.type == JOYBUTTONUP:
                    # yes
                    if e.button == 4: # L1
                        if player.mode == "quit":
                            playing = False
                        elif player.mode == "restart":
                            main()
                    # no
                    elif e.button == 5: # R1
                        if player.mode == "quit" or player.mode == "restart":
                            player.mode = "play"

        elif player.mode == "next level":
            if level == "userlevel":
                main()
            else:
                if level == MAX_LEVELS:
                    text = "Congratulations! You beat the game."
                else:
                    text = "Loading level %d . . ." % (level + 1)
                level += 1
                label = myfont.render(text, 1, (WHITE))

                labelrect = label.get_rect()
                labelrect.centerx = screen.get_rect().centerx
                labelrect.centery = screen.get_rect().centery

                screen.blit(splash2, (HALF_WIDTH - 497, 0))
                screen.blit(label, labelrect)

                pygame.display.update()
                pygame.time.wait(800)

                play(level)

        elif player.mode == "game over":
            fading = True
            while fading:
                fadeScreen.fill(BLACK)
                fsalpha += 1
                fadeScreen.set_alpha(fsalpha)

                label = myfont.render("GAME OVER", 1, (WHITE))
                fadeScreen.blit(label, (350,300))

                screen.blit(fadeScreen, (0,0))
                pygame.display.update()
                if fsalpha == 50:
                    fading = False
            main()

        pygame.display.update()
    pygame.quit()

class Level(object):
    def __init__(self, name, level, background, lightOn):
        self.name = name
        self.level = level
        self.bg = background
        self.light = lightOn # True or False

class LevelEditorAsset(object):
    def __init__(self):
        pass

class EditorCamera(LevelEditorAsset):
    def __init__(self):
        LevelEditorAsset.__init__(self)
        self.xshifted = 0
        self.yshifted = 0
        self.rows = MIN_NUM_ROWS
        self.cols = MIN_NUM_COLS

    def update(self, keys, gameAssets, player):
        if keys['up'] == True:
            self.yshifted += 1
        if keys['down'] == True:
            self.yshifted -= 1
        if keys['left'] == True:
            self.xshifted += 1
        if keys['right'] == True:
            self.xshifted -= 1

        self.isLegalShift(self.xshifted, self.yshifted)

        # shift all the blocks in gameAssets
        for e in gameAssets:
            e.x += self.xshifted*32
            e.y += self.yshifted*32

        # shift the player
        if player != None:
            player.x += self.xshifted*32
            player.y += self.yshifted*32

    def shiftView(self, other):
        if isLegalShift(dx, dy):
            other.x += self.dx
            other.y += self.dy

    def isLegalShift(self, xshifted, yshifted):
        if self.xshifted > 0:
            self.xshifted = 0
        if self.xshifted < MIN_NUM_COLS - self.cols:
            self.xshifted = MIN_NUM_COLS - self.cols
        if self.yshifted > 0:
            self.yshifted = 0
        if self.yshifted < MIN_NUM_ROWS - self.rows:
            self.yshifted = MIN_NUM_ROWS - self.rows

    def reset(self):
        self.rows = MIN_NUM_ROWS
        self.cols = MIN_NUM_COLS

    def resetShifts(self):
        self.xshifted = 0
        self.yshifted = 0

    def changeRows(self, val):
        self.rows += val
        if self.rows < MIN_NUM_ROWS:
            self.rows = MIN_NUM_ROWS

    def changeCols(self, val):
        self.cols += val
        if self.cols < MIN_NUM_COLS:
            self.cols = MIN_NUM_COLS

class EditorLevel(LevelEditorAsset):
    def __init__(self, rows, cols):
        LevelEditorAsset.__init__(self)
        self.mouseHeld = False
        self.rows = rows
        self.cols = cols
        self.board = []
        for i in range(rows):
            self.board.append(" " * cols)

        # fills the outermost ring of blocks with "P", rest is all empty
        for row in range(rows):
            for col in range(cols):
                if row == 0 or col == 0 or row == rows - 1 or col == cols - 1:
                    self.replace(row, col, "P")

    def addBlock(self, pos, block, editorCam):
        x, y = pos
        x += abs(editorCam.xshifted) * 32
        y += abs(editorCam.yshifted) * 32
        row, col = self.getRowCol(x, y)
        if row != 0 and col != 0 and row != len(self.board) - 1 and col != len(self.board[0]) - 1:
            self.replace(row, col, block)

    def getRowCol(self, x, y):
        col = x // 32
        row = y // 32
        return row, col

    def replace(self, row, col, block):
        if block == "X":
            for i in range(len(self.board)):
                self.board[i] = self.board[i].replace("X", " ")
        line = self.board[row]
        lineIndex = col
        newChar = block
        line = line[:lineIndex] + newChar + line[lineIndex + 1:]
        self.board[row] = line

class EditorGrid(LevelEditorAsset):
    def __init__(self):
        LevelEditorAsset.__init__(self)
        self.x = 0
        self.y = 0
        self.rows = WIN_HEIGHT // 32 + 2
        self.cols = WIN_WIDTH // 32 + 2
        self.gridOn = True

    def update(self, surface):
        if self.gridOn:
            for row in range(self.rows):
                pygame.draw.line(surface, GRAY, (0, row*32), (self.cols*32, row*32))
            for col in range(self.cols):
                pygame.draw.line(surface, GRAY, (col*32, 0), (col*32, self.rows*32))

class BlockHeld(LevelEditorAsset):
    def __init__(self):
        LevelEditorAsset.__init__(self)
        self.selectedBlock = None
        self.strEq = None

    # block is an EditorBlock button object
    def hold(self, block):
        self.selectedBlock = block.image
        self.strEq = block.strEq

class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)

def makeCamera(view, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = view
    l, t, _, _ = -l+HALF_WIDTH, -t+HALF_HEIGHT, w, h

    l = min(0, l)
    l = max(-(view.width-WIN_WIDTH), l)
    t = max(-(view.height-WIN_HEIGHT), t)
    t = min(0, t)
    return Rect(l, t, w, h)

class GameAsset(pygame.sprite.Sprite):
    fill = (WHITE)
    def __init__(self, x, y, w, h, fill = fill):
        pygame.sprite.Sprite.__init__(self)
        self.image = Surface((w, h)).convert_alpha()
        self.image.convert()
        self.image.fill(fill)
        self.rect = Rect(x, y, w, h)
        self.x = self.rect.x
        self.y = self.rect.y
        self.w = self.rect.w
        self.h = self.rect.h

class UI(GameAsset):
    def __init__(self, x, y, w, h):
        GameAsset.__init__(self, x, y, w, h)
        self.hover = False
        self.clickedOn = False

    def isInsideButton(self, pos):
        x, y = pos
        return True if self.rect.left < x < self.rect.right and self.rect.top < y < self.rect.bottom else False

    def executeTask(self, player):
        pass

    def hoverOn(self):
        pass

    def hoverOff(self):
        pass

class TestUserLevel(UI):
    def __init__(self, x, y, w, h, image):
        UI.__init__(self, x, y, w, h)
        self.image = image
        self.clickedOn = False

    def testLevel(self, level):
        if self.isLegalLevel(level):
            play("userlevel")

    def isLegalLevel(self, level):
        for row in level:
            if "X" in row: #test to make sure player is put in the level
                saveLevelFile("userLevels.txt", level, "userlevel1")
                return True
        return False

class EditorBlock(UI):
    def __init__(self, x, y, w, h, image, strEq):
        UI.__init__(self, x, y, w, h)
        self.image = image
        self.strEq = strEq

class MenuButton(UI):
    def __init__(self, x, y, w, h, nextMode, images):
        UI.__init__(self, x, y, w, h)
        self.images = images
        self.image = self.images[0]
        self.clickedOn = False
        self.nextMode = nextMode

    def executeTask(self, player):
        if self.nextMode == "menu":
            main()
        else:
            player.mode = self.nextMode

    def hoverOn(self):
        self.image = self.images[1]

    def hoverOff(self):
        self.image = self.images[0]

class SaveLoadButton(UI):
    def __init__(self, x, y, w, h, image, function):
        UI.__init__(self, x, y, w, h)
        self.image = image
        self.function = function

    def executeTask(self, level):
        if self.function == "save":
            self.save(level)
        elif self.function == "load":
            loaded = self.load()
            return loaded["userlevel1"]

    def save(self, level):
        # file name, level list, and level name
        saveLevelFile("userLevels.txt", level, "userlevel1")

    def load(self):
        return loadLevelFile("userLevels.txt")

class CreatorBgSelect(UI):
    def __init__(self, x, y, w, h, image, selectedImage):
        UI.__init__(self, x, y, w, h)
        self.image = image
        self.selectedImage = selectedImage

    def hoverOn(self):
        self.hover = True

    def hoverOff(self):
        self.hover = False

    def executeTask(self, player):
        player.bgSelected = self.selectedImage

class RowColButton(UI):
    def __init__(self, x, y, w, h, image, rowCol, val):
        UI.__init__(self, x, y, w, h)
        self.image = image
        self.rowCol = rowCol
        self.val = val

    def hoverOn(self):
        self.hover = True

    def hoverOff(self):
        self.hover = False

    def executeTask(self, editorCam):
        if self.rowCol == "row":
            editorCam.changeRows(self.val)
        elif self.rowCol == "col":
            editorCam.changeCols(self.val)

class Movable(GameAsset):
    def __init__(self, x, y, w, h):
        GameAsset.__init__(self, x, y, w, h)
        self.dx = 0
        self.dy = 0
        self.onGround = False
        self.hit = False
        self.inContact = 0

    def limitMaxSpeed(self, maxSpeed):
        if self.dx > maxSpeed:
            self.dx = maxSpeed
        if self.dx < -maxSpeed:
            self.dx = -maxSpeed
        if self.dy > maxSpeed:
            self.dy = maxSpeed
        if self.dy < -maxSpeed:
            self.dy = -maxSpeed

class Boss(Movable):
    def __init__(self, x, y):
        Movable.__init__(self, x, y, 48, 48)
        self.image = pygame.image.load('boss1.png')

    def move(self, player, platforms, enemies, currLevel):
        if self.rect.x < player.rect.x:
            self.dx += .3
        else:
            self.dx-= .3
        if self.rect.y < player.rect.y:
            self.dy += .3
        else:
            self.dy-= .3
        self.limitMaxSpeed(10)
        self.rect.x += self.dx
        self.rect.y += self.dy

    def update(self):
        pass

class Enemy(Movable):
    def __init__(self, x, y):
        Movable.__init__(self, x, y, 38, 48)
        self.index = 0
        self.images = []
        a = pygame.image.load('drone1.png')
        b = pygame.image.load('drone2.png')
        a.convert_alpha()
        b.convert_alpha()
        self.images.append(a)
        self.images.append(b)
        self.image = self.images[self.index]

    def move(self, player, platforms, enemies, currLevel):
        if self.rect.x < player.rect.x:
            self.dx += .3
        else:
            self.dx-= .3
        if self.rect.y < player.rect.y:
            self.dy += .3
        else:
            self.dy-= .3
        self.rect.x += self.dx
        self.collide(self.dx, 0, platforms, enemies, currLevel)
        self.rect.y += self.dy
        self.collide(0, self.dy, platforms, enemies, currLevel)
        self.limitMaxSpeed(5)
        self.inContact = 0

    def collide(self, dx, dy, platforms, enemies, currLevel):
        for p in platforms:
            self.findCollision(dx, dy, p)

        # nearbyBlocks = self.getNearbyBlocks(currLevel)
        # for p in nearbyBlocks:
        #     self.findCollision2(dx, dy, p)
        for e in enemies:
            if not(e is self):
                self.findCollision(dx, dy, e)

    def findCollision2(self, dx, dy, other):
        print(self.rect.bottom, other.top, self.rect.top,other.bottom)
        if (not ((self.rect.bottom < other.top) or (self.rect.top > other.bottom)) or
            not ((self.rect.left > other.right) or (self.rect.right < other.left))):
            if dx > 0:
                self.rect.right = other.left
                # print("collide right")
                self.inContact += 1
            if dx < 0:
                self.rect.left = other.right
                # print("collide left")
                self.inContact += 1
            if dy > 0:
                self.rect.bottom = other.top
                self.dy = 0
                # print("collide ground")
                self.inContact += 1
            if dy < 0:
                self.rect.top = other.bottom
                self.dy = 0
                # print("collide top")
                self.inContact += 1
    def findCollision(self, dx, dy, other):
        if pygame.sprite.collide_rect(self, other):
            if (not isinstance(other, NonCollideable) and
                not isinstance(other, Aid) and
                not isinstance(other, Fuel)):
                if dx > 0:
                    self.rect.right = other.rect.left
                    # print("collide right")
                    self.inContact += 1
                if dx < 0:
                    self.rect.left = other.rect.right
                    # print("collide left")
                    self.inContact += 1
                if dy > 0:
                    self.rect.bottom = other.rect.top
                    self.dy = 0
                    # print("collide ground")
                    self.inContact += 1
                if dy < 0:
                    self.rect.top = other.rect.bottom
                    self.dy = 0
                    # print("collide top")
                    self.inContact += 1

    def getNearbyBlocks(self, currLevel):
        x, y = self.rect.center
        row, col = y // 32, x // 32
        maxRow, maxCol = len(currLevel) - 1, len(currLevel[0]) - 1
        nearbyBlocks = []

        for i in range(max(-5, -row), min(6, maxRow - row + 1)):
            for j in range(max(-5, -col), min(6, maxCol - col + 1)):
                if currLevel[row+i][col+j] in ("P", "K"):
                    nearbyBlocks.append(Rect(col*32, row*32, 32, 32))
        print(nearbyBlocks)
        return nearbyBlocks

    def update(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

class Player(Movable):
    def __init__(self, x, y):
        Movable.__init__(self, x, y, 48, 48)
        shipSprite = pygame.image.load('ship.png')
        self.image = shipSprite
        self.lightRadius = 400

        self.bleeding = False
        self.entityToRemove = []
        self.jumpsLeft = 3
        self.canJump = True
        self.checkedCollision = False

        self.lightR = 150
        self.lightG = 150
        self.lightB = 130

        self.health = 10

        self.mode = "menu"
        self.hacksOff = True
        self.bgSelected = None

    def jump(self):
        if self.jumpsLeft > 0:
            self.dy = -15
            self.jumpsLeft -= 1
        self.checkedCollision = False

        if self.dy < -15:
            self.dy = -15

    def update(self, keys, platforms, enemies):
        # print("doubleJump, ", self.jumpsLeft)
        # print("onGround, ", self.onGround)
        if not self.hit:
            if keys['down']:
                pass
            if keys['left']:
                self.dx = -10
            if keys['right']:
                self.dx = 10
            if keys['down']:
                self.dy += 4
            if not self.onGround:
                # only accelerate with gravity if in the air
                # going up
                if self.dy <= 0:
                    self.dy += 1
                # coming back down (a bit faster)
                elif self.dy > 0:
                    self.dy += 1.1
                # max falling speed
                if self.dy > 18: self.dy = 18
            if not(keys['left'] or keys['right']):
                self.dx = 0
        else:
            self.dy = -13
            self.hit = False
            self.lightG = 0
            self.lightB = 0
            self.health -= 2
            self.onGround = False
            self.checkedCollision = False
        self.rect.left += self.dx
        self.collide(self.dx, 0, platforms, enemies)
        self.rect.top += self.dy

        if keys['left'] or keys['right'] or keys['up'] or keys['down']:
            self.checkedCollision = False
        # print(self.onGround)

        if not self.checkedCollision:
            self.onGround = False
            self.collide(0, self.dy, platforms, enemies)
            if self.onGround == True:
                self.checkedCollision = True

    def collide(self, dx, dy, platforms, enemies):
        for e in enemies:
            if pygame.sprite.collide_mask(self, e) != None:
                self.mode = "game over"
        for p in platforms:
            if not isinstance(p, NonCollideable):
                if pygame.sprite.collide_rect(self, p):
                    # print("Collision detected and we are on the ground:", self.onGround)
                    # print("And we hit ", p)
                    # if isinstance(p, NonCollideable):
                        # print("\t", p.blockType)
                    if isinstance(p, Fuel):
                        self.lightRadius = 400
                        platforms.remove(p)
                        self.entityToRemove = p
                    elif isinstance(p, Aid):
                        self.bleeding = False
                        platforms.remove(p)
                        self.entityToRemove = p
                        self.health += 5
                        if self.health > 10:
                            self.health = 10
                    else:
                        if isinstance(p, ExitBlock):
                            pygame.event.post(pygame.event.Event(QUIT))
                            self.mode = "next level"
                        if isinstance(p, HarmfulBlock):
                            self.bleeding = True
                            self.hit = True
                        if dx > 0:
                            self.rect.right = p.rect.left
                            # print("collide right")
                        if dx < 0:
                            self.rect.left = p.rect.right
                            # print("collide left")
                        if dy > 0:
                            self.rect.bottom = p.rect.top
                            self.onGround = True
                            # print("we hit the ground", self.onGround)
                            self.dy = 0
                            # self.jumpsLeft = True
                            # print("collide ground")
                            self.jumpsLeft = 3
                        if dy < 0:
                            self.rect.top = p.rect.bottom
                            self.dy = 0
                            # print("collide top")

class Aid(GameAsset):
    def __init__(self, x, y, image):
        GameAsset.__init__(self, x, y, 32, 32)
        self.image = image

class Fuel(GameAsset):
    def __init__(self, x, y, image):
        GameAsset.__init__(self, x, y, 32, 32)
        self.image = image

class Bg(GameAsset):
    def __init__(self, x, y):
        fill = WHITE
        GameAsset.__init__(self, x, y, 0, 0, fill)

class Platform(GameAsset):
    def __init__(self, x, y, type=None):
        fill = (135,206,250)
        GameAsset.__init__(self, x, y, 32, 32, fill)
        self.type = type

class PlatformTop(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)

class PlatformInside(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)

class PlatformInside2(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)

class ExitBlock(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)
        self.image = pygame.image.load('exit_block.png')

class HarmfulBlock(GameAsset):
    def __init__(self, x, y):
        fill = (128,128,128)
        GameAsset.__init__(self, x, y, w=32, h=32, fill = fill)

class Spike(HarmfulBlock):
    def __init__(self, x, y):
        HarmfulBlock.__init__(self, x, y)

class ToxicBlock(HarmfulBlock):
    def __init__(self, x, y, type=None):
        HarmfulBlock.__init__(self, x, y)
        self.type=type

class Animation(GameAsset):
    def __init__(self, x, y):
        GameAsset.__init__(self, x, y, 32, 32)
        self.index = 0
        self.images = []
        self.image = None
        self.stop = False

class AnimationOnce(Animation):
    def __init__(self, x, y):
        Animation.__init__(self, x, y)

    def animate(self):
        self.index += 1
        if self.index >= len(self.images):
            self.stopAnimating()
        else:
            self.image = self.images[self.index]

    def stopAnimating(self):
        self.stop = True

class AnimationLooped(Animation):
    def __init__(self, x, y):
        Animation.__init__(self, x, y)

    def animate(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

class ToxicBubble(AnimationLooped):
    def __init__(self, x, y):
        Animation.__init__(self, x, y)
        self.images.append(pygame.image.load('toxic_bubble_1.png'))
        self.images.append(pygame.image.load('toxic_bubble_2.png'))
        self.images.append(pygame.image.load('toxic_bubble_3.png'))
        self.images.append(pygame.image.load('toxic_bubble_4.png'))
        self.images.append(pygame.image.load('toxic_bubble_5.png'))
        self.images.append(pygame.image.load('toxic_bubble_6.png'))
        self.images.append(pygame.image.load('toxic_bubble_7.png'))
        self.images.append(pygame.image.load('toxic_bubble_8.png'))
        self.images.append(pygame.image.load('toxic_bubble_9.png'))
        self.images.append(pygame.image.load('toxic_bubble_10.png'))
        self.images.append(pygame.image.load('toxic_bubble_11.png'))
        self.image = self.images[self.index]

class SmokePuff(AnimationOnce):
    def __init__(self, x, y):
        Animation.__init__(self, x, y)
        self.images.append(pygame.image.load('smoke_puff_1.png'))
        self.images.append(pygame.image.load('smoke_puff_2.png'))
        self.images.append(pygame.image.load('smoke_puff_3.png'))
        self.images.append(pygame.image.load('smoke_puff_4.png'))
        self.images.append(pygame.image.load('smoke_puff_5.png'))
        self.images.append(pygame.image.load('smoke_puff_6.png'))
        self.images.append(pygame.image.load('smoke_puff_7.png'))
        self.image = self.images[self.index]

class NonCollideable(GameAsset):
    def __init__(self, x, y, blockType):
        fill = (0,0,0)
        GameAsset.__init__(self, x, y, 32, 32, fill)
        self.blockType = blockType        

class BgStone(NonCollideable):
    def __init__(self, x, y):
        NonCollideable.__init__(self, x, y)

class Grass(NonCollideable):
    def __init__(self, x, y):
        NonCollideable.__init__(self, x, y)

class Flowers(NonCollideable):
    def __init__(self, x, y):
        NonCollideable.__init__(self, x, y)

class Mushrooms(NonCollideable):
    def __init__(self, x, y):
        NonCollideable.__init__(self, x, y)

class GameVars(object):
    def __init__(self):
        self.level = 1

if __name__ == "__main__":
    main()