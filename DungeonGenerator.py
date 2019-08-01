
import math
import random
import sys
import time

#################
# Configuration #
#################

USE_CUSTOM_SEED     = True
CUSTOM_SEED         = 1070403273516726580#1337420

solidTile           = '#'
roomTile            = '`'
tunnelTile          = ' '
doorTile            = 'O'

PRINT_TO_FILE       = True
FILE_NAME           = "dungeonNeat.txt"

MIN_VERTICAL_RO0M_SIZE      = 5
MIN_HORIZONTAL_ROOM_SIZE    = 5

MAX_VERTICAL_ROOM_SIZE      = 6#8
MAX_HORIZONTAL_ROOM_SIZE    = 6#8

WORLD_SIZE_VERTICAL         = 48#128
WORLD_SIZE_HORIZONTAL       = 48#128

ROOM_COUNT                  = 24#96
MAX_DOORS_PER_ROOM          = 3

BENCHMARK           = False
BENCHMARK_RUNS      = 10

# Feature levels disable the effect the feature has on the world,
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
    centerA = center(a)
    centerB = center(b)

    x = a[0] - b[0]
    y = a[1] - b[1]

    return math.sqrt(x**2 + y**2)

def distManhatten(a, b):
    centerA = center(a)
    centerB = center(b)

    x = a[0] - b[0]
    y = a[1] - b[1]

    return abs(x) + abs(y)

def getPathDist(path):
    return path[2]

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

def fill(world, tile, startY, endY, startX, endX):
    if not FEATURE_ROOMS:
        return
    for y in range(startY, endY):
        for x in range(startX, endX):
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
        if ri == roomE or ri == roomE2:
            continue
        
        room = rooms[ri]
        
        if not (startX > room[RIGHT] or endX < room[LEFT] or \
                yPos > room[BOTTOM] or yPos < room[TOP]):
            if DEBUG_PATHS:
                print(f"Horizontal intersection. Line: Y: ({yPos}) X: ({startX}-{endX}) Room: #{ri} {room}")
            return True
    
    return False

def intersectLineV(world, rooms, startY, endY, xPos, roomE, roomE2):
    for ri in range(0, len(rooms)):
        if ri == roomE or ri == roomE2:
            continue
        
        room = rooms[ri]
        
        if not (xPos > room[RIGHT] or xPos < room[LEFT] or \
                startY > room[BOTTOM] or endY < room[TOP]):
            if DEBUG_PATHS:
                print(f"Vertical intersection. Line: Y: ({startY}-{endY}) X: ({xPos}) Room: #{ri} {room}")
            return True
        
    return False

def main():
    world = _2da(WORLD_SIZE_HORIZONTAL, WORLD_SIZE_VERTICAL, solidTile)
    seed = CUSTOM_SEED if USE_CUSTOM_SEED else random.randrange(sys.maxsize)

    print(f"Map seed (ew): {seed}")
    random.seed(seed)
    
    # Step 1: Room generation
    
    rooms = [None for a in range(ROOM_COUNT)]
    
    t0 = time.time_ns()
    
    for ri in range(ROOM_COUNT):
        attempt = True
        while attempt:
            startx = random.randrange(0, WORLD_SIZE_HORIZONTAL - MAX_HORIZONTAL_ROOM_SIZE)
            starty = random.randrange(0, WORLD_SIZE_VERTICAL - MAX_VERTICAL_ROOM_SIZE)
            endx = min(startx + random.randrange(MIN_HORIZONTAL_ROOM_SIZE, MAX_HORIZONTAL_ROOM_SIZE),
                       WORLD_SIZE_HORIZONTAL)
            endy = min(starty + random.randrange(MIN_VERTICAL_RO0M_SIZE, MAX_VERTICAL_ROOM_SIZE),
                       WORLD_SIZE_VERTICAL)
            
            #               LEFT, TOP, RIGHT, BOTTOM
            currentRoom = (startx, starty, endx, endy)
            
            if ri > 0:
                intersection = False
                for i in range(0, ri):
                    if intersectRect(currentRoom, rooms[i]):
                        intersection = True
                        break
                
                if intersection:
                    continue
            
            attempt = False
            rooms[ri] = currentRoom
            fill(world, roomTile, starty, endy, startx, endx)
    
    if DEBUG_ROOMS:
        print("Rooms:")
        for ri in range(ROOM_COUNT):
            print(f"#{ri}: " + str(rooms[ri]))
    
    # Step 2: Kruskal's Algorithm
    
    allPaths = []
    
    for ri in range(ROOM_COUNT):
        for ri0 in range(ri + 1, ROOM_COUNT):
            p = (ri, ri0, distManhatten(rooms[ri], rooms[ri0]))
            allPaths.append(p)
    
    allPaths.sort(key=getPathDist)
    
    parents = [i for i in range(ROOM_COUNT)]
    ranks = [0] * ROOM_COUNT
    paths = []
    doorsPerRoom = [0] * ROOM_COUNT
    
    for p in allPaths:
        if doorsPerRoom[p[0]] == MAX_DOORS_PER_ROOM or doorsPerRoom[p[1]] == MAX_DOORS_PER_ROOM:
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
        startRoom = rooms[p[0]]
        endRoom = rooms[p[1]]
        
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
            
            tunnelY = random.randrange(horTunStart, horTunEnd)
            
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
            
            tunnelX = random.randrange(verTunStart, verTunEnd)
            
            fillLineV(world, tunnelTile, startY, endY, tunnelX, doorTile, doorTile)
            
        else:
            if DEBUG_PATHS:
                print("Diagonal needed")
            startVertical = random.random() > 0.5
            
            vStartTile = tunnelTile
            vEndTile = tunnelTile
            hStartTile = tunnelTile
            hEndTile = tunnelTile
            
            attempts = 0
            
            while attempts < 2:
                startRY = random.randrange(startRoom[TOP] + 1, startRoom[BOTTOM] - 1)
                startRX = random.randrange(startRoom[LEFT] + 1, startRoom[RIGHT] - 1)
                endRY = random.randrange(endRoom[TOP] + 1, endRoom[BOTTOM] - 1)
                endRX = random.randrange(endRoom[LEFT] + 1, endRoom[RIGHT] - 1)
                
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
                
                if intersectLineV(world, rooms, startX, endX, tunnelY, p[0], p[1]) or \
                   intersectLineH(world, rooms, startY, endY, tunnelX, p[0], p[1]):
                    
                    attempts += 1
                    startVertical = not startVertical
                    if DEBUG_PATHS:
                        print(f"Found intersection when digging diagonal path between {rooms[p[0]]} and {rooms[p[1]]}")
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
        
        for i in range(0, int(WORLD_SIZE_HORIZONTAL / 4)):
            print(f"{i*4}\t", end = "")
        print()
        print("\t\t", end = "")
        for i in range(0, int(WORLD_SIZE_HORIZONTAL / 4)):
            print("|\t", end = "")
        
        print()
        
        for y in range(0, WORLD_SIZE_VERTICAL):
            # Double up the X axis so that things look more square
            print(f"{y}\t\t" + ''.join([val for pair in zip(world[y], world[y]) for val in pair]))
    
    if BENCHMARK:
        print(f"Dungeon generated in {timeElapsed}")
        return timeElapsed
    
    if PRINT_TO_FILE:
        with open(FILE_NAME, 'wt') as f:
            f.write(f"Seed: {seed}\n")
            f.write(f"World size: {WORLD_SIZE_VERTICAL}x{WORLD_SIZE_HORIZONTAL} (Height x Width)\n")
            f.write(f"Room count: {ROOM_COUNT}\n")
            f.write(f"Room size: {MIN_HORIZONTAL_ROOM_SIZE}x{MIN_VERTICAL_RO0M_SIZE} - {MAX_HORIZONTAL_ROOM_SIZE}x{MAX_VERTICAL_ROOM_SIZE}\n")
            f.write(f"Maximum doors: {MAX_DOORS_PER_ROOM}\n")
            for y in range(0, WORLD_SIZE_VERTICAL):
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
