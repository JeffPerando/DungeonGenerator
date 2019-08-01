
from math import *

import random
import sys
import time

#################
# Configuration #
#################

USE_CUSTOM_SEED     = False
CUSTOM_SEED         = 1070403273516726580#1337420

solidTile           = '#'
roomTile            = '`'
tunnelTile          = ' '
doorTile            = 'O'
bossWallTile        = '@'

PRINT_TO_FILE       = False
FILE_NAME           = "dungeonBossTest.txt"

MIN_ROOM_HEIGHT             = 3#5
MIN_ROOM_WIDTH              = 3#5
MAX_ROOM_HEIGHT             = 6#8
MAX_ROOM_WIDTH              = 6#8

MIN_BOSS_RADIUS             = 10.5
MAX_BOSS_RADIUS             = 14.5

WORLD_HEIGHT                = 48#128
WORLD_WIDTH                 = 48#128

ROOM_COUNT                  = 24#96
MAX_DOORS_PER_ROOM          = 3


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
DEBUG_GEN           = True
# Debugs room generation. Will print a list of generated
# rooms, specifically their bounds.
DEBUG_ROOMS         = False
# Debugs pathing between rooms. Prints off the finished
# minimum weight spanning tree, and where paths are generated.
DEBUG_KRUSKAL       = False
# Prints when a path is generated
DEBUG_PATHS         = False

##################
# Program beyond #
#   this point   #
##################

# IMPORTANT CONSTANTS
LEFT        = 0
TOP         = 1
RIGHT       = 2
BOTTOM      = 3

def _2da(x, y, v):
    return [[v] * x for b in range(y)]

def intersectRect(ba, bb):
    return not (ba[LEFT] > bb[RIGHT] or ba[RIGHT] < bb[LEFT] or \
                ba[TOP] > bb[BOTTOM] or ba[BOTTOM] < bb[TOP])

def center(room):
    return (round(room[LEFT] + ((room[RIGHT] - room[LEFT]) / 2)),
            round(room[TOP] + ((room[BOTTOM] - room[TOP]) / 2)))

def distEuclid(a, b):
    x = a[0] - b[0]
    y = a[1] - b[1]

    return sqrt(x**2 + y**2)

def distManhatten(a, b):
    centerA = center(a)
    centerB = center(b)

    x = centerA[0] - centerB[0]
    y = centerA[1] - centerB[1]

    return abs(x) + abs(y)

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

def fill(world, tile, bounds):
    if not FEATURE_ROOMS:
        return
    for y in range(bounds[TOP], bounds[BOTTOM]):
        for x in range(bounds[LEFT], bounds[RIGHT]):
            world[y][x] = tile

def fillLineH(world, tile, startX, endX, yPos, firstTile = None, lastTile = None):
    if DEBUG_PATHS:
        print(f"Horizontal:\tY: ({yPos}), X: ({startX}-{endX}), start tile: \'{firstTile}\', end tile: \'{lastTile}\'")
    if not FEATURE_PATHS:
        return
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
    if DEBUG_PATHS:
        print(f"Vertical:\tY: ({startY}-{endY}), X: ({xPos}), start tile: \'{firstTile}\', end tile: \'{lastTile}\'")
    if not FEATURE_PATHS:
        return
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

def intersectLineH(world, rooms, startX, endX, yPos, roomE, roomE2):
    for ri in range(0, len(rooms)):
        if ri == roomE or ri == roomE2[0]:
            continue
        
        room = rooms[ri]
        roomBounds = room.bounds
        
        if not (startX > roomBounds[RIGHT] or endX < roomBounds[LEFT] or \
                yPos > roomBounds[BOTTOM] or yPos < roomBounds[TOP]):
            if DEBUG_PATHS:
                print(f"Horizontal intersection. Line: Y: ({yPos}) X: ({startX}-{endX}) Room: #{ri} {room}")
            return True
    
    return False

def intersectLineV(world, rooms, startY, endY, xPos, roomE, roomE2):
    for ri in range(0, len(rooms)):
        if ri == roomE or ri == roomE2:
            continue
        
        room = rooms[ri]
        roomBounds = room.bounds
        
        if not (xPos > roomBounds[RIGHT] or xPos < roomBounds[LEFT] or \
                startY > roomBounds[BOTTOM] or endY < roomBounds[TOP]):
            if DEBUG_PATHS:
                print(f"Vertical intersection. Line: Y: ({startY}-{endY}) X: ({xPos}) Room: #{ri} {room}")
            return True
        
    return False

class Room:
    def __init__(self):
        self.bounds = [0] * 4
        self.doorBounds = []
        self.tile = ' '
    
    def generate(self, rng):
        self.bounds[TOP] = rng.randrange(0, WORLD_HEIGHT - MAX_ROOM_HEIGHT)
        self.bounds[LEFT] = rng.randrange(0, WORLD_WIDTH - MAX_ROOM_WIDTH)
        self.bounds[BOTTOM] = min(self.bounds[TOP] + rng.randrange(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT), WORLD_HEIGHT)
        self.bounds[RIGHT] = min(self.bounds[LEFT] + rng.randrange(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH), WORLD_WIDTH)
        
        self.doorBounds.append(self.bounds)
    
    def populate(self, world):
        fill(world, self.tile, self.bounds)

    def intersectsWithRect(self, rect):
        return rectIntersect(self.bounds, rect)

class BossRoom(Room):
    def __init__(self):
        super().__init__()
        self.radius = 0.0
        self.center = (0, 0)
    
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
        
        topCube[TOP] = self.bounds[TOP]
        topCube[LEFT] = centerX - (ceil((MIN_ROOM_WIDTH) / 2))
        topCube[BOTTOM] = topCube[TOP] + MIN_ROOM_HEIGHT + 1
        topCube[RIGHT] = centerX + (ceil((MIN_ROOM_WIDTH) / 2)) + 1
        
        leftCube[TOP] = centerY - (ceil((MIN_ROOM_HEIGHT) / 2))
        leftCube[LEFT] = self.bounds[LEFT]
        leftCube[BOTTOM] = centerY + (ceil((MIN_ROOM_WIDTH) / 2)) + 1
        leftCube[RIGHT] = leftCube[LEFT] + MIN_ROOM_WIDTH + 1
        
        bottomCube[TOP] = self.bounds[BOTTOM] - MIN_ROOM_HEIGHT
        bottomCube[LEFT] = topCube[LEFT]
        bottomCube[BOTTOM] = self.bounds[BOTTOM]
        bottomCube[RIGHT] = topCube[RIGHT]
        
        rightCube[TOP] = leftCube[TOP]
        rightCube[LEFT] = self.bounds[RIGHT] - MIN_ROOM_WIDTH
        rightCube[BOTTOM] = leftCube[BOTTOM]
        rightCube[RIGHT] = self.bounds[RIGHT]
        
        self.doorBounds = [topCube, leftCube, bottomCube, rightCube]
    
    def populate(self, world):
        for y in range(self.bounds[TOP], self.bounds[BOTTOM]):
            for x in range(self.bounds[LEFT], self.bounds[RIGHT]):
                if distEuclid((y, x), self.center) <= self.radius:
                    world[y][x] = self.tile
                else:
                    world[y][x] = bossWallTile
        
        for bound in self.doorBounds:
            fill(world, self.tile, bound)
    
    def intersectsWithRect(self, rect):
        for cube in self.doorBounds:
            if intersectRect(rect, cube):
                return True
        
        if distEuclid((rect[TOP], rect[LEFT]), self.center) <= self.radius:
            return True
        if distEuclid((rect[TOP], rect[RIGHT]), self.center) <= self.radius:
            return True
        if distEuclid((rect[BOTTOM], rect[LEFT]), self.center) <= self.radius:
            return True
        if distEuclid((rect[BOTTOM], rect[RIGHT]), self.center) <= self.radius:
            return True

class RoomTableData:
    def __init__(self, factory, wt, pwm, rank):
        self.newRoom = factory
        self.weight = wt
        self.perWorldMin = pwm
        self.priority = rank
    def test(self):
        return
# Technically should be a configuration option, but who really wants to
# fuck with the room generation that badly? Come on min, leave it alone
ROOM_WEIGHTS = [RoomTableData(BossRoom.__class__, 5, 1, 99),
                RoomTableData(Room.__class__, 95, 0, 0)]

ROOM_WEIGHTS.sort(reverse = True, key = lambda data : data.priority)

def main():
    world = _2da(WORLD_WIDTH, WORLD_HEIGHT, solidTile)
    rng = random.Random()
    seed = CUSTOM_SEED if USE_CUSTOM_SEED else rng.randrange(sys.maxsize)
    
    print(f"Map seed (ew): {seed}")
    rng.seed(seed)
    
    # Step 1: Room generation
    
    t0 = time.time_ns()
    
    rooms = [None for a in range(ROOM_COUNT)]
    mandatoryRooms = []
    
    totalWeight = 0
    
    for data in ROOM_WEIGHTS:
        totalWeight += data.weight
        for i in range(data.perWorldMin):
            mandatoryRooms.append(data.newRoom)
    
    for ri in range(ROOM_COUNT):
        attempt = True
        while attempt:
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
                roomData = RoomTableData(Room.__class__, 0, 0, 0)

            print(RoomTableData.__attrs__)
            #factory = roomData.newRoom
            #currentRoom = factory()
            return
            if ri > 0:
                intersection = False
                for i in range(0, ri):
                    if intersectRect(currentRoom.bounds, rooms[i].bounds):
                        intersection = True
                        break
                
                if intersection:
                    continue
            
            attempt = False
            rooms[ri] = currentRoom
            currentRoom.populate(world)
    
    if DEBUG_ROOMS:
        print("Rooms:")
        for ri in range(ROOM_COUNT):
            print(f"#{ri}: " + str(rooms[ri].bounds))
    
    # Step 2: Kruskal's Algorithm
    
    doorBounds = []# (roomIndex, doorBounds)
    allPaths = []
    
    for ri in range(ROOM_COUNT):
        room = rooms[ri]
        for bound in room.doorBounds:
            allDoorBounds.append((ri, bound))
    
    for ri in range(len(allDoorBounds)):
        for ri0 in range(ri + 1, len(allDoorBounds)):
            doorBound = doorBounds[ri]
            doorBoundOther = doorBounds[ri0]
            if doorBound[0] == doorBoundOther[0]:
                continue
            p = (doorBound, doorBoundOther, distManhatten(doorBound[1], doorBoundOther[1]))
            allPaths.append(p)
    
    allPaths.sort(key = lambda x : x[2])
    
    parents = [i for i in range(ROOM_COUNT)]
    ranks = [0] * ROOM_COUNT
    paths = []
    doorsPerRoom = [0] * ROOM_COUNT
    
    for p in allPaths:
        if doorsPerRoom[p[0][0]] == MAX_DOORS_PER_ROOM or doorsPerRoom[p[1][0]] == MAX_DOORS_PER_ROOM:
            continue
        # Could add a condition to check for intersecting rooms, but that would have
        # limited use, and wouldn't be very practical. Not to mention make the code
        # run significantly slower.
        if find(parents, p[0]) != find(parents, p[1]):
            paths.append(p)
            union(parents, ranks, p[0], p[1])
            doorsPerRoom[p[0]] += 1
            doorsPerRoom[p[1]] += 1
    
    if DEBUG_KRUSKAL:
        print("Minimum weight spanning tree:")
        for p in paths:
            print(p)
    
    # Step 3: Build Paths
    
    if DEBUG_PATHS:
        print("Paths:")
    
    for p in paths:
        startRoom = doorBounds[p[0]]
        endRoom = doorBounds[p[1]]
        
        horTunStart = max(startRoom[TOP], endRoom[TOP])
        horTunEnd = min(startRoom[BOTTOM], endRoom[BOTTOM])
        
        verTunStart = max(startRoom[LEFT], endRoom[LEFT])
        verTunEnd = min(startRoom[RIGHT], endRoom[RIGHT])
        
        # vertical tunnel
        startY = 0
        endY = 0
        tunnelX = 0
        
        # horizontal tunnel
        startX = 0
        startX = 0
        tunnelY = 0
        
        if horTunStart < horTunEnd:
            if DEBUG_PATHS:
                print("Horizontal needed")
            if startRoom[LEFT] > endRoom[LEFT]:
                startX = endRoom[RIGHT]
                endX = startRoom[LEFT]
            else:
                startX = startRoom[RIGHT]
                endX = endRoom[LEFT]
            
            tunnelY = rng.randrange(horTunStart, horTunEnd)
            
            fillLineH(world, tunnelTile, startX, endX, tunnelY, doorTile, doorTile)
            
        elif verTunStart < verTunEnd:
            if DEBUG_PATHS:
                print("Vertical needed")
            if startRoom[TOP] > endRoom[TOP]:
                startY = endRoom[BOTTOM]
                endY = startRoom[TOP]
            else:
                startY = startRoom[BOTTOM]
                endY = endRoom[TOP]
            
            tunnelX = rng.randrange(verTunStart, verTunEnd)
            
            fillLineV(world, tunnelTile, startY, endY, tunnelX, doorTile, doorTile)
            
        else:
            if DEBUG_PATHS:
                print("Diagonal needed")
            startVertical = rng.random() > 0.5
            
            vStartTile = tunnelTile
            vEndTile = tunnelTile
            hStartTile = tunnelTile
            hEndTile = tunnelTile
            
            attempts = 0
            
            while attempts < 2:
                startRY = rng.randrange(startRoom[TOP] + 1, startRoom[BOTTOM] - 1)
                startRX = rng.randrange(startRoom[LEFT] + 1, startRoom[RIGHT] - 1)
                endRY = rng.randrange(endRoom[TOP] + 1, endRoom[BOTTOM] - 1)
                endRX = rng.randrange(endRoom[LEFT] + 1, endRoom[RIGHT] - 1)
                
                if startVertical:
                    startY = min(startRoom[BOTTOM], endRY)
                    endY = max(startRoom[TOP], endRY)
                    tunnelX = startRX
                    
                    startX = min(endRoom[RIGHT], tunnelX)
                    endX = max(endRoom[LEFT], startRX + 1)
                    tunnelY = endRY
                    
                    vStartTile = doorTile if startY == startRoom[BOTTOM] else tunnelTile
                    vEndTile = doorTile if endY == startRoom[TOP] else tunnelTile
                    hStartTile = doorTile if startX == endRoom[RIGHT] else tunnelTile
                    hEndTile = doorTile if endX == endRoom[LEFT] else tunnelTile
                else:
                    startX = min(startRoom[RIGHT], endRX)
                    endX = max(startRoom[LEFT], endRX)
                    tunnelY = startRY
                    
                    startY = min(endRoom[BOTTOM], tunnelY)
                    endY = max(endRoom[TOP], startRY + 1)
                    tunnelX = endRX
                    
                    vStartTile = doorTile if startY == endRoom[BOTTOM] else tunnelTile
                    vEndTile = doorTile if endY == endRoom[TOP] else tunnelTile
                    hStartTile = doorTile if startX == startRoom[RIGHT] else tunnelTile
                    hEndTile = doorTile if endX == startRoom[LEFT] else tunnelTile
                
                if intersectLineV(world, rooms, startX, endX, tunnelY, p[0][0], p[1][0]) or \
                   intersectLineH(world, rooms, startY, endY, tunnelX, p[0][0], p[1][0]):
                    
                    attempts += 1
                    startVertical = not startVertical
                    if DEBUG_PATHS:
                        print(f"Found intersection when digging diagonal path between {rooms[p[0][0]]} and {rooms[p[1][0]]}")
                    continue
                # I would go ahead and cancel the tunnel if we can't find a non-intersecting path,
                # but that would make parts of the map unobtainable without mining tools.
                # So we just say 'sod it' and build the tunnel anyway.
                break
            
            fillLineV(world, tunnelTile, startY, endY, tunnelX, vStartTile, vEndTile)
            fillLineH(world, tunnelTile, startX, endX, tunnelY, hStartTile, hEndTile)
            
    
    # Final step: Present
    
    t1 = time.time_ns()
    timeElapsed = (t1 - t0) / 1000000
    
    if DEBUG_GEN:
        print("\t\t", end = "")
        
        for i in range(0, int(WORLD_WIDTH / 4)):
            print(f"{i*4}\t", end = "")
        print()
        print("\t\t", end = "")
        for i in range(0, int(WORLD_WIDTH / 4)):
            print("|\t", end = "")
        
        print()
        
        for y in range(0, WORLD_HEIGHT):
            # Double up the X axis so that things look more square
            print(f"{y}\t\t" + ''.join([val for pair in zip(world[y], world[y]) for val in pair]))
    
    if BENCHMARK:
        print(f"Dungeon generated in {timeElapsed}")
        return timeElapsed
    
    if PRINT_TO_FILE:
        with open(FILE_NAME, 'wt') as f:
            f.write(f"Seed: {seed}\n")
            f.write(f"World size: {WORLD_HEIGHT}x{WORLD_WIDTH} (Height x Width)\n")
            f.write(f"Room count: {ROOM_COUNT}\n")
            f.write(f"Room size: {MIN_ROOM_WIDTH}x{MIN_ROOM_HEIGHT} - {MAX_ROOM_WIDTH}x{MAX_ROOM_HEIGHT}\n")
            f.write(f"Maximum doors: {MAX_DOORS_PER_ROOM}\n")
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
