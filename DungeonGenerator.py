
from copy import *
from math import *

import random
import sys
import time

#################
# Configuration #
#################

USE_CUSTOM_SEED     = True
CUSTOM_SEED         = 4956553581393908256#1337420

solidTile           = '#'
roomTile            = '`'
tunnelTile          = ' '
doorTile            = 'O'
bossWallTile        = '@'
chestTile           = '$'
monsterTile         = '^'

PRINT_TO_FILE       = False
FILE_NAME           = "dungeonBossTest4.txt"

MIN_ROOM_HEIGHT             = 3#5
MIN_ROOM_WIDTH              = 3#5
MAX_ROOM_HEIGHT             = 6#8
MAX_ROOM_WIDTH              = 6#8

MIN_BOSS_RADIUS             = 6.5
MAX_BOSS_RADIUS             = 14.5

WORLD_HEIGHT                = 128
WORLD_WIDTH                 = 48

ROOM_COUNT                  = 16#96

MAX_CHEST_COUNT             = 2

BENCHMARK           = False
BENCHMARK_RUNS      = 10

# These disable the effect the feature has on the world,
# but doesn't outright disable the feature entirely. Generation
# will work exactly the same, and the data itself will still be
# in the game world as though it's there.
FEATURE_ROOMS       = True
FEATURE_PATHS       = True
FEATURE_ROOM_DECOR  = True

# Debugs dungeon generation itself. After generation,
# the finished dungeon will be printed out in the console.
PRINT_FINAL_DUNGEON         = True

PRINT_AFTER_EVERY_ROOM      = False
PRINT_AFTER_EVERY_PATH      = False

# Debugs room generation. Will print a list of generated
# rooms, specifically their bounds.
DEBUG_ROOMS         = False
# Debugs pathing between rooms. Prints off the finished
# minimum weight spanning tree, and where paths are generated.
DEBUG_KRUSKAL       = False
# Prints when a vertical path is generated
DEBUG_V_PATHS       = False
DEBUG_H_PATHS       = False
DEBUG_D_PATHS       = False

##################
# Program beyond #
#   this point   #
##################

# IMPORTANT CONSTANTS
LEFT        = 0
TOP         = 1
RIGHT       = 2
BOTTOM      = 3

# Helper functions

# Creates a 2D array
def _2da(x, y, v):
    return [[v] * x for b in range(y)]

# Finds the center of a boundary
def center(room):
    return (round(room[LEFT] + ((room[RIGHT] - room[LEFT]) / 2)),
            round(room[TOP] + ((room[BOTTOM] - room[TOP]) / 2)))

# Distance algorithms
def distEuclid(a, b):
    x = a[0] - b[0]
    y = a[1] - b[1]

    return sqrt(x**2 + y**2)

def distManhatten(a, b):
    x = a[0] - b[0]
    y = a[1] - b[1]

    return abs(x) + abs(y)

# Kruskal's algorithm

def find(parents, room):
    if parents[room] == room:
        return room
    return find(parents, parents[room])

def union(parents, ranks, a, b):
    aroot = find(parents, a)
    broot = find(parents, b)

    if ranks[aroot] == ranks[broot]:
        parents[broot] = aroot
        ranks[aroot] += 1
    elif ranks[aroot] < ranks[broot]:
        parents[aroot] = broot
    elif ranks[aroot] > ranks[broot]:
        parents[broot] = aroot

# Fill functions

def fill(world, tile, bounds):
    for y in range(bounds[TOP], bounds[BOTTOM]):
        for x in range(bounds[LEFT], bounds[RIGHT]):
            world[y][x] = tile

def fillLineH(world, tile, startX, endX, yPos, firstTile = None, lastTile = None):
    if DEBUG_H_PATHS:
        print(f"Horizontal:\tY: ({yPos}), X: ({startX}-{endX}), start tile: \'{firstTile}\', end tile: \'{lastTile}\'")
    if firstTile == None:
        firstTile = tile
    if lastTile == None:
        lastTile = tile
    end = endX - startX - 1
    count = 0
    for x in range(startX, endX):
        tileUsed = tile
        if count == 0:
            tileUsed = firstTile
        elif count == end:
            tileUsed = lastTile
        world[yPos][x] = tileUsed
        count += 1

def fillLineV(world, tile, startY, endY, xPos, firstTile = None, lastTile = None):
    if DEBUG_V_PATHS:
        print(f"Vertical:\tY: ({startY}-{endY}), X: ({xPos}), start tile: \'{firstTile}\', end tile: \'{lastTile}\'")
    if firstTile == None:
        firstTile = tile
    if lastTile == None:
        lastTile = tile
    end = endY - startY - 1
    count = 0
    for y in range(startY, endY):
        tileUsed = tile
        if count == 0:
            tileUsed = firstTile
        elif count == end:
            tileUsed = lastTile
        world[y][xPos] = tileUsed
        count += 1

# Intersection checks

def intersectRect(ba, bb):
    return not (ba[LEFT] > bb[RIGHT] or ba[RIGHT] < bb[LEFT] or \
                ba[TOP] > bb[BOTTOM] or ba[BOTTOM] < bb[TOP])

def intersectRectPoint(rect, point):
    X = 0
    Y = 1
    return rect[LEFT] <= point[X] and rect[TOP] <= point[Y] and rect[RIGHT] > point[X] and rect[BOTTOM] > point[Y]

def intersectRectLine(rect, startPoint, endPoint):
    return intersectRectPoint(rect, startPoint) or intersectRectPoint(rect, endPoint)

def intersectLineH(world, rooms, roomCount, startX, endX, yPos, roomE, roomE2):
    for ri in range(0, roomCount):
        if ri == roomE or ri == roomE2:
            continue
        
        room = rooms[ri]
        roomBounds = room.bounds
        
        if intersectRectLine(roomBounds, (startX, yPos), (endX, yPos)):
            if DEBUG_H_PATHS:
                print(f"Horizontal intersection. Line: Y: ({yPos}) X: ({startX}-{endX}) Room: #{ri} {roomBounds}")
            return True
    
    return False

def intersectLineV(world, rooms, roomCount, startY, endY, xPos, roomE, roomE2):
    for ri in range(0, roomCount):
        if ri == roomE or ri == roomE2:
            continue
        
        room = rooms[ri]
        roomBounds = room.bounds
        
        if intersectRectLine(roomBounds, (xPos, startY), (xPos, endY)):
            if DEBUG_V_PATHS:
                print(f"Vertical intersection. Line: Y: ({startY}-{endY}) X: ({xPos}) Room: #{ri} {roomBounds}")
            return True
    
    return False

# World print

def printWorld(world, height, width):
    print("\t\t", end = "")
        
    for i in range(0, int(width / 4)):
        print(f"{i*4}\t", end = "")
    print()
    print("\t\t", end = "")
    for i in range(0, int(width / 4)):
        print("|\t", end = "")
    
    print()
    
    for y in range(0, height):
        # Double up the X axis so that things look more square
        print(f"{y}\t\t" + ''.join([val for pair in zip(world[y], world[y]) for val in pair]))

# Classes

class Room:
    def __init__(self):
        self.bounds = [0] * 4
        self.doorBounds = []
        self.tile = roomTile
        self.maxDoors = 3
        self.chests = []
    
    def generate(self, rng):
        self.bounds[LEFT] = rng.randrange(0, WORLD_WIDTH - MAX_ROOM_WIDTH)
        self.bounds[TOP] = rng.randrange(0, WORLD_HEIGHT - MAX_ROOM_HEIGHT)
        self.bounds[RIGHT] = min(self.bounds[LEFT] + rng.randrange(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH), WORLD_WIDTH)
        self.bounds[BOTTOM] = min(self.bounds[TOP] + rng.randrange(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT), WORLD_HEIGHT)
        
        self.chestCount = rng.randrange(0, MAX_CHEST_COUNT)
        self.chests = [None] * self.chestCount
        
        for i in range(0, self.chestCount):
            self.chests[i] = (rng.randrange(self.bounds[LEFT], self.bounds[RIGHT]), rng.randrange(self.bounds[TOP], self.bounds[BOTTOM]))
        
        self.doorBounds.append(self.bounds)
    
    def populate(self, world):
        fill(world, self.tile, self.bounds)
    
    def populateDecor(self, world):
        for chest in self.chests:
            world[chest[1]][chest[0]] = chestTile
    
    def intersectsWithRect(self, rect):
        return intersectRect(self.bounds, rect)

class BossRoom(Room):
    def __init__(self):
        super().__init__()
        self.radius = 0.0
        self.center = (0, 0)
        self.maxDoors = 2
        self.boxes = None
    
    def generate(self, rng):
        self.radius = floor(rng.uniform(MIN_BOSS_RADIUS, MAX_BOSS_RADIUS))
        
        sizeY = round(2 * MIN_ROOM_HEIGHT + 2 * self.radius)
        sizeX = round(2 * MIN_ROOM_WIDTH + 2 * self.radius)
        halfSizeY = floor(sizeY / 2)
        halfSizeX = floor(sizeX / 2)
        
        centerY = rng.randrange(halfSizeY, WORLD_HEIGHT - halfSizeY)
        centerX = rng.randrange(halfSizeX, WORLD_WIDTH - halfSizeX)
        
        self.center = (centerY, centerX)
        
        self.bounds[TOP] = centerY - halfSizeY
        self.bounds[LEFT] = centerX - halfSizeX
        self.bounds[BOTTOM] = centerY + halfSizeY
        self.bounds[RIGHT] = centerX + halfSizeX
        
        topCube = [0] * 4
        leftCube = [0] * 4
        bottomCube = [0] * 4
        rightCube = [0] * 4
        
        topCube[LEFT] = centerX - (ceil((MIN_ROOM_WIDTH) / 2))
        topCube[TOP] = self.bounds[TOP]
        topCube[RIGHT] = centerX + (ceil((MIN_ROOM_WIDTH) / 2)) + 1
        topCube[BOTTOM] = topCube[TOP] + MIN_ROOM_HEIGHT + 1
        
        leftCube[LEFT] = self.bounds[LEFT]
        leftCube[TOP] = centerY - (ceil((MIN_ROOM_HEIGHT) / 2))
        leftCube[RIGHT] = leftCube[LEFT] + MIN_ROOM_WIDTH + 1
        leftCube[BOTTOM] = centerY + (ceil((MIN_ROOM_WIDTH) / 2)) + 1
        
        bottomCube[LEFT] = topCube[LEFT]
        bottomCube[TOP] = self.bounds[BOTTOM] - MIN_ROOM_HEIGHT
        bottomCube[RIGHT] = topCube[RIGHT]
        bottomCube[BOTTOM] = self.bounds[BOTTOM]
        
        rightCube[LEFT] = self.bounds[RIGHT] - MIN_ROOM_WIDTH
        rightCube[TOP] = leftCube[TOP]
        rightCube[RIGHT] = self.bounds[RIGHT]
        rightCube[BOTTOM] = leftCube[BOTTOM]
        
        self.boxes = [leftCube, topCube, rightCube, bottomCube]
        
        self.doorBounds = deepcopy(self.boxes)
        self.doorBounds[LEFT][RIGHT] = leftCube[LEFT] + 1
        self.doorBounds[TOP][BOTTOM] = topCube[TOP] + 1
        self.doorBounds[RIGHT][LEFT] = rightCube[RIGHT] - 1
        self.doorBounds[BOTTOM][TOP] = bottomCube[BOTTOM] - 1
    
    def populate(self, world):
        for y in range(self.bounds[TOP], self.bounds[BOTTOM]):
            for x in range(self.bounds[LEFT], self.bounds[RIGHT]):
                if distEuclid((y, x), self.center) <= self.radius:
                    world[y][x] = self.tile
                else:
                    world[y][x] = bossWallTile
        
        for bound in self.boxes:
            fill(world, self.tile, bound)
    
    def intersectsWithRect(self, rect):
        for cube in self.boxes:
            if intersectRect(rect, cube):
                return True
        
        if distEuclid((rect[TOP], rect[LEFT]), self.center) <= self.radius + 1:
            return True
        if distEuclid((rect[TOP], rect[RIGHT]), self.center) <= self.radius + 1:
            return True
        if distEuclid((rect[BOTTOM], rect[LEFT]), self.center) <= self.radius + 1:
            return True
        if distEuclid((rect[BOTTOM], rect[RIGHT]), self.center) <= self.radius + 1:
            return True

class RoomTableData:
    def __init__(self, factory, wt, pwm, rank):
        self.newRoom = factory
        self.weight = wt
        self.perWorldMin = pwm
        self.priority = rank

# Technically should be a configuration option, but who really wants to
# fuck with the room generation that badly? Come on min, leave it alone
ROOM_WEIGHTS = [RoomTableData(Room, 95, 0, 0),
                RoomTableData(BossRoom, 5, 1, 99)]

ROOM_WEIGHTS.sort(reverse = True, key = lambda data : data.priority)

def main():
    world = _2da(WORLD_WIDTH, WORLD_HEIGHT, solidTile)
    seed = CUSTOM_SEED if USE_CUSTOM_SEED else random.randrange(sys.maxsize)
    
    print(f"Map seed (ew): {seed}")
    random.seed(seed)
    
    # Step 1: Room generation
    
    t0 = time.time_ns()
    
    rooms = [None] * ROOM_COUNT
    generators = [None] * ROOM_COUNT
    roomCount = ROOM_COUNT
    maxDoors = [0] * ROOM_COUNT
    mandatoryRooms = []
    
    totalWeight = 0
    
    for data in ROOM_WEIGHTS:
        totalWeight += data.weight
        for i in range(data.perWorldMin):
            mandatoryRooms.append(data)
    
    for ri in range(ROOM_COUNT):
        attempts = 0
        roomData = None
        
        if ri < len(mandatoryRooms):
            roomData = mandatoryRooms[ri]
        else:
            weight = rng.randrange(0, totalWeight)
            
            for data in ROOM_WEIGHTS:
                weight -= data.weight
                if weight < 0:
                    roomData = data
                    break
        
        if roomData == None:
            roomData = RoomTableData(Room, 0, 0, 0)
        
        currentRoom = roomData.newRoom()
        rng = random.Random()
        roomSeed = random.randrange(sys.maxsize)
        rng.seed(roomSeed)
        
        while attempts < 128:
            currentRoom.generate(rng)
            
            if ri > 0:
                intersection = False
                for i in range(0, ri):
                    if intersectRect(rooms[i].bounds, currentRoom.bounds):
                        intersection = True
                        break
                
                if intersection:
                    attempts += 1
                    continue
                
            rooms[ri] = currentRoom
            maxDoors[ri] = currentRoom.maxDoors
            
            if FEATURE_ROOMS:
                currentRoom.populate(world)
            
            if FEATURE_ROOM_DECOR:
                currentRoom.populateDecor(world)
            
            if PRINT_AFTER_EVERY_ROOM:
                printWorld(world, WORLD_HEIGHT, WORLD_WIDTH)
            break
            
        if attempts == 128:
            print("Took too long to generate a room")
            roomCount = ri
            break
    
    if DEBUG_ROOMS:
        print("Rooms:")
        for ri in range(roomCount):
            print(f"#{ri}: " + str(rooms[ri].bounds))
        print("Maximum doors:")
        print(maxDoors)
    
    # Step 2: Kruskal's Algorithm
    
    allDoorBounds = []# (roomIndex, doorBounds)
    allPaths = []
    
    for ri in range(roomCount):
        room = rooms[ri]
        for bound in room.doorBounds:
            allDoorBounds.append((ri, bound))
    
    for bi in range(len(allDoorBounds)):
        for bi0 in range(bi + 1, len(allDoorBounds)):
            doorBound = allDoorBounds[bi]
            doorBoundOther = allDoorBounds[bi0]
            if doorBound[0] == doorBoundOther[0]:
                continue
            p = (doorBound, doorBoundOther, distEuclid(center(doorBound[1]), center(doorBoundOther[1])))
            allPaths.append(p)
    
    allPaths.sort(key = lambda x : x[2])
    
    parents = [i for i in range(roomCount)]
    ranks = [0] * roomCount
    paths = []
    doorCounts = [0] * roomCount
    
    for p in allPaths:
        firstRoomIndex = p[0][0]
        otherRoomIndex = p[1][0]
        # Could add a condition to check for intersecting rooms, but that would have
        # limited use, and wouldn't be very practical. Not to mention make the code
        # run significantly slower.
        if doorCounts[firstRoomIndex] == maxDoors[firstRoomIndex] or doorCounts[otherRoomIndex] == maxDoors[otherRoomIndex]:
            continue
        if find(parents, firstRoomIndex) != find(parents, otherRoomIndex):
            paths.append(p)
            union(parents, ranks, firstRoomIndex, otherRoomIndex)
            
            doorCounts[firstRoomIndex] += 1
            doorCounts[otherRoomIndex] += 1
    
    root = 0
    rootOptions = []
    for i in range(roomCount):
        # There will always be a room with 1 door, because there can't be a cycle in the spanning tree.
        if doorCounts[i] == 1:
            rootOptions.append(i)
    
    root = random.choice(rootOptions)
    
    if DEBUG_KRUSKAL:
        print(f"Parents: {parents}")
        print("Minimum weight spanning tree:")
        for p in paths:
            print(p)
        print("Door counts:")
        for dc in doorCounts:
            print(dc)
        print(f"Root: #{root}, {rooms[root].bounds}")
    
    # Step 3: Build Paths
    
    if DEBUG_V_PATHS or DEBUG_H_PATHS or DEBUG_D_PATHS:
        print("Paths:")
    
    for p in paths:
        startRoom = p[0]
        endRoom = p[1]
        
        startRoomIndex = startRoom[0]
        endRoomIndex = endRoom[0]
        
        startBounds = startRoom[1]
        endBounds = endRoom[1]
        
        horTunYStart = max(startBounds[TOP], endBounds[TOP])
        horTunYEnd = min(startBounds[BOTTOM], endBounds[BOTTOM])
        
        verTunXStart = max(startBounds[LEFT], endBounds[LEFT])
        verTunXEnd = min(startBounds[RIGHT], endBounds[RIGHT])
        
        # vertical tunnel
        startY = 0
        endY = 0
        tunnelX = 0
        
        # horizontal tunnel
        startX = 0
        startX = 0
        tunnelY = 0
        
        if horTunYStart < horTunYEnd:
            if DEBUG_H_PATHS:
                print("Horizontal needed")
            if startBounds[LEFT] > endBounds[LEFT]:
                startX = endBounds[RIGHT]
                endX = startBounds[LEFT]
            else:
                startX = startBounds[RIGHT]
                endX = endBounds[LEFT]
            
            tunnelY = random.randrange(horTunYStart, horTunYEnd)
            
            if FEATURE_PATHS:
                fillLineH(world, tunnelTile, startX, endX, tunnelY, doorTile, doorTile)
            
        elif verTunXStart < verTunXEnd:
            if DEBUG_V_PATHS:
                print("Vertical needed")
            if startBounds[TOP] > endBounds[TOP]:
                startY = endBounds[BOTTOM]
                endY = startBounds[TOP]
            else:
                startY = startBounds[BOTTOM]
                endY = endBounds[TOP]
            
            tunnelX = random.randrange(verTunXStart, verTunXEnd)
            
            if FEATURE_PATHS:
                fillLineV(world, tunnelTile, startY, endY, tunnelX, doorTile, doorTile)
            
        else:
            if DEBUG_D_PATHS:
                print(f"Diagonal needed between {startBounds} and {endBounds}")
            startVertical = random.random() > 0.5
            
            vStartTile = tunnelTile
            vEndTile = tunnelTile
            hStartTile = tunnelTile
            hEndTile = tunnelTile
            
            attempts = 0

            # TODO make algorithm smarter
            # TODO implement an optional diagonal tunnel
            # NOTE: If the attempt count is too low, it will still intersect some rooms even if it doesn't have to.
            # That's because it randomly selects new positions and gives up too easily.
            while attempts < 32:
                addOneV = startBounds[TOP] == endBounds[BOTTOM] or startBounds[BOTTOM] == endBounds[TOP]
                addOneH = startBounds[LEFT] == endBounds[RIGHT] or startBounds[RIGHT] == endBounds[LEFT]
                
                startRY = rng.randrange(startBounds[TOP] + addOneV, startBounds[BOTTOM] - addOneV)
                startRX = rng.randrange(startBounds[LEFT] + addOneH, startBounds[RIGHT] - addOneH)
                endRY = rng.randrange(endBounds[TOP] + addOneV, endBounds[BOTTOM] - addOneV)
                endRX = rng.randrange(endBounds[LEFT] + addOneH, endBounds[RIGHT] - addOneH)
                
                if startVertical:
                    startY = min(startBounds[BOTTOM], endRY)
                    endY = max(startBounds[TOP], endRY)
                    tunnelX = startRX
                    
                    startX = min(endBounds[RIGHT], tunnelX)
                    endX = max(endBounds[LEFT], startRX + 1)
                    tunnelY = endRY
                    
                    vStartTile = doorTile if startY == startBounds[BOTTOM] else tunnelTile
                    vEndTile = doorTile if endY == startBounds[TOP] else tunnelTile
                    hStartTile = doorTile if startX == endBounds[RIGHT] else tunnelTile
                    hEndTile = doorTile if endX == endBounds[LEFT] else tunnelTile
                else:
                    startX = min(startBounds[RIGHT], endRX)
                    endX = max(startBounds[LEFT], endRX)
                    tunnelY = startRY
                    
                    startY = min(endBounds[BOTTOM], tunnelY)
                    endY = max(endBounds[TOP], startRY + 1)
                    tunnelX = endRX
                    
                    vStartTile = doorTile if startY == endBounds[BOTTOM] else tunnelTile
                    vEndTile = doorTile if endY == endBounds[TOP] else tunnelTile
                    hStartTile = doorTile if startX == startBounds[RIGHT] else tunnelTile
                    hEndTile = doorTile if endX == startBounds[LEFT] else tunnelTile
                
                if intersectLineV(world, rooms, roomCount, startY, endY, tunnelX, startRoomIndex, endRoomIndex) or \
                   intersectLineH(world, rooms, roomCount, startX, endX, tunnelY, startRoomIndex, endRoomIndex):
                    attempts += 1
                    startVertical = not startVertical
                    if DEBUG_D_PATHS:
                        print(f"Found intersection when digging diagonal path between {startBounds} and {endBounds}")
                    continue
                # I would go ahead and cancel the tunnel if we can't find a non-intersecting path,
                # but that would make parts of the map unobtainable without mining tools.
                # So we just say 'sod it' and build the tunnel anyway.
                break
            
            if FEATURE_PATHS:
                fillLineV(world, tunnelTile, startY, endY, tunnelX, vStartTile, vEndTile)
                fillLineH(world, tunnelTile, startX, endX, tunnelY, hStartTile, hEndTile)
        
        if PRINT_AFTER_EVERY_PATH:
            printWorld(world, WORLD_HEIGHT, WORLD_WIDTH)
    
    # Final step: Present
    
    t1 = time.time_ns()
    timeElapsed = (t1 - t0) / 1000000
    
    if PRINT_FINAL_DUNGEON:
        printWorld(world, WORLD_HEIGHT, WORLD_WIDTH)
    
    if BENCHMARK:
        print(f"Dungeon generated in {timeElapsed}")
        return timeElapsed
    
    if PRINT_TO_FILE:
        with open(FILE_NAME, 'wt') as f:
            f.write(f"Seed: {seed}\n")
            f.write(f"World size: {WORLD_HEIGHT}x{WORLD_WIDTH} (Height x Width)\n")
            f.write(f"Room count: {roomCount}\n")
            f.write(f"Room size: {MIN_ROOM_WIDTH}x{MIN_ROOM_HEIGHT} - {MAX_ROOM_WIDTH}x{MAX_ROOM_HEIGHT}\n")
            for y in range(0, WORLD_HEIGHT):
                f.write(''.join([val for pair in zip(world[y], world[y]) for val in pair]) + '\n')

if BENCHMARK:
    totalTime = 0.0
    for i in range(BENCHMARK_RUNS):
        timeTaken = main()
        totalTime += timeTaken
    
    avgTime = (totalTime / BENCHMARK_RUNS)
    print(f"Average time: {avgTime}")
else:
    main()
