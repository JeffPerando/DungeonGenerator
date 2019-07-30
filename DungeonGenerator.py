
import random
import time

MIN_HORIZONTAL_ROOM_SIZE =  6
MIN_VERTICAL_RO0M_SIZE =    6

MAX_HORIZONTAL_ROOM_SIZE =  12
MAX_VERTICAL_ROOM_SIZE =    12

WORLD_SIZE_HORIZONTAL = 48
WORLD_SIZE_VERTICAL =   48

ROOM_COUNT = 10

LEFT =      0
TOP =       1
RIGHT =     2
BOTTOM =    3

def _2da(x, y, v):
    return [[v for a in range(x)] for b in range(y)]

def intersectRect(ba, bb):
    return not (ba[LEFT] > bb[RIGHT] or ba[RIGHT] < bb[LEFT] or ba[TOP] > bb[BOTTOM] or ba[BOTTOM] < bb[TOP])

def main():
    world = _2da(WORLD_SIZE_HORIZONTAL, WORLD_SIZE_VERTICAL, '#')
    
    rooms = [None for a in range(ROOM_COUNT)]
    
    t0 = time.time_ns()
    
    for ri in range(ROOM_COUNT):
        attempt = True
        while attempt:
            # left
            startx = random.randrange(0, WORLD_SIZE_HORIZONTAL - MAX_HORIZONTAL_ROOM_SIZE)
            # top
            starty = random.randrange(0, WORLD_SIZE_VERTICAL - MAX_VERTICAL_ROOM_SIZE)
            
            # right
            endx = min(startx + random.randrange(MIN_HORIZONTAL_ROOM_SIZE, MAX_HORIZONTAL_ROOM_SIZE), WORLD_SIZE_HORIZONTAL)
            # bottom
            endy = min(starty + random.randrange(MIN_HORIZONTAL_ROOM_SIZE, MAX_HORIZONTAL_ROOM_SIZE), WORLD_SIZE_HORIZONTAL)
            
            currentRoom = (startx, starty, endx, endy)
            
            if ri > 0:
                intersection = False
                for i in range(0, ri):
                    otherRoom = rooms[i]
                    
                    if intersectRect(currentRoom, otherRoom):
                        intersection = True
                        break
                if intersection:
                    continue
            
            attempt = False
            
            rooms[ri] = currentRoom
            
            for x in range(startx, endx):
                for y in range(starty, endy):
                    tile = '@'
                    if x == startx or x == endx - 1 or y == starty or y == endy - 1:
                        tile = '*'
                    world[x][y] = tile
    
    t1 = time.time_ns()
    elapsed = (t1 - t0) / 1000
    
    print(f"That took {elapsed} ms")
    
    for ri in range(ROOM_COUNT):
        print(rooms[ri])
    
    for x in range(0, WORLD_SIZE_HORIZONTAL):
        for y in range(0, WORLD_SIZE_VERTICAL):
            print(world[x][y], end = "")
        
        print()

main()
