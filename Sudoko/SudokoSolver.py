#import numpy
import pandas
import copy

# Perhaps this can be done using a brute force tree search, but I
# have always wanted to create a working, semi-intelligent Sudoko
# solver, and this kata is an opportunity to do so.  I used the
# pattern rules and terminology from sudoku9x9.com.
#
# Here's the approach.  Each cell in the grid will be represented by a
# set of possible values.  If we know exactly what value goes into the
# cell, its set will be of size 1.  If we can get the entire grid down
# to 81 one-element sets unique by row, column, and 3x3 square, we've
# found a valid solution.
#
# There are a few basic rules for ruling out cell values.  (A more
# sophisticated Sudoko solver might define many more, based on complex
# pattern matching.)  Whenever we get 'stuck', we'll hypothesize the
# value for one cell, then see where it leads us.  To ensure we find
# all valid solutions without doing unnecessary work, the search will
# start in the upper right corner and proceed by (1) increasing numeric
# cell value, (2) row, and (3) column.  When we've exhausted the search
# tree, we're finished.
    
def sudoku_solver(puzzle):
    debugLevel = 0

    if (debugLevel >= 1):
        printGrid(puzzle, False)

    # game validation
    #
    if ( (len(puzzle) != 9)
         or not all(len(row) == 9 for row in puzzle)):
        raise ValueError("puzzle is not a 9x9 grid")
    
    badvals = { col for row in puzzle for col in row if (not isinstance(col, int) or col < 0 or col > 9) }
    if ( badvals ):
        raise ValueError("invalid value(s) in puzzle:" + str(badvals))
    
    
    # Set up the data structures we need.  gameNines consists of our 81 cells
    # broken down into nine groups of nines:
    #   [0:9]   = rows
    #   [9:18]  = cols
    #   [19:27] = squares
    # Note that gameRows contains the original 81 sets; everything else simply
    # references existing sets.  For an explanation of gameTriplets, see setupGame().
    #
    startState = [ [ set( range(1, 10) ) if (cell == 0) else { cell } for cell in row ]
                   for row in puzzle ]
    gameNines, gameTriplets = setupGame(startState)

    if (debugLevel >= 1):
        print("Starting...\n")
        printGrid(gameNines[0:9])
        printGrid(gameTriplets, False)
        
    # for each loop, we'll apply our reduction rules (which are not exhaustive;
    # some of the known complex rules are very difficult to code up).  If we 
    # finish with one solution, we'll return it.  If the puzzle is unsolvable,
    # we'll throw an exception.  Else, we'll take the first unresolved cell
    # and clone the game |cell| times, each with one of its possible values
    # filled in, and recurse.
    #
    validSolutions = []
    gameQueue = [ [ gameNines, gameTriplets ] ]
    
    while (gameQueue):
        gameNines, gameTriplets = gameQueue.pop(0)
        
        if (debugLevel >= 1):
            print("Now solving (" + str(len(gameQueue)) + " remain):")
            printSimpleGrid(gameNines[0:9])

        reduceResult = applyAndValidate(gameNines, gameTriplets, debugLevel=debugLevel)

        if (debugLevel >= 1):
            print("Done game (" + str(len(gameQueue)) + " remain). Reduction result = " + str(reduceResult))
            printSimpleGrid(gameNines[0:9])
            print("")

        # add a successful solution to our list
        #
        if (reduceResult == 1):
            validSolutions.append( [ [ list(cell)[0] for cell in row ] for row in gameNines[0:9] ] )
        
        # still unsolved?  We'll need to hypothesize the first unresolved cell and
        # try each possibility
        #
        elif (reduceResult == 0):
            
            # get the first unresolved cell's coordinates and values
            #
            hypoCoords = None
            hypoValues = set()

            for iRow, row in enumerate(gameNines[0:9]):
                for iCol, cell in enumerate(row):
                    if (len(cell) > 1):
                        hypoCoords = (iRow, iCol)
                        hypoValues = cell
                        break
                if (hypoCoords):
                    break
            
            # clone the game n times, each with a set value in the target
            # cell, and add them to the game queue
            #
            for n in hypoValues:
                newGame = copy.deepcopy(gameNines[0:9])
                newGame[hypoCoords[0]][hypoCoords[1]] &= { n }
                gameQueue.append(list(setupGame(newGame)))
                
                if (debugLevel >= 1):
                    print("Spawning at " + str(hypoCoords) + " using value " + str(n) + " from " + str(hypoValues))
                    print("Added new game to queue (len=" + str(len(gameQueue)) + "):")
                    printSimpleGrid(newGame)
            
    # well?.....
    #
    if (len(validSolutions) == 1):
        if (debugLevel >= 1):
            print("The solution:")
            printGrid(validSolutions[0], False)
        
        return validSolutions[0]
    
    elif (len(validSolutions) == 0):
        raise Exception("No valid solutions")
        
    else:
        raise Exception("Multiple solutions")



# Given a set of game rows (either from the original input or
# from a deep copy), set up and return all necessary data
# structures.  Multi-return value is (gameNines, gameTriplets).
# Note that the initial set of rows are used as-is as the first
# nine "nines".
#
def setupGame(inRows):
    
    # the "nines" - rows[0..9], columns[9..18] and squares[18..27]
    #
    gameRows = inRows
    gameCols = [list(a) for a in zip(*gameRows)]
    gameSquares = []
    
    for r in range(0, 9, 3):
        for c in range(0, 9, 3):
            gameSquares += [ gameRows[r][c:c+3] + gameRows[r+1][c:c+3] + gameRows[r+2][c:c+3] ]

    gameNines = gameRows + gameCols + gameSquares
    
    # For Rule 3 ("locked candidates") it's useful to break down the grid into 54 "triplets",
    # comprising the intersection of a square and a row or column.  Each triplet is linked
    # to its six "sister" cells in the same square, and also to its six sisters in the same
    # row/col. Format: [ [triplet], [lineSisters], [squareSisters] ]
    
    gameTriplets = []
    
    for ix, row in enumerate(gameRows):
        for t in range(0, 9, 3):
            triplet = row[t:t+3]
            rowSisters = row[0:t] + row[t+3:]
            square = gameSquares[(ix // 3) * 3 + t // 3]
            squareSisters = square[0:3 * (ix % 3)] + square[3 * (ix % 3) + 3:]
            gameTriplets += [ [ triplet, rowSisters, squareSisters ] ]

    for ix, col in enumerate(gameCols):
        for t in range(0, 9, 3):
            triplet = col[t:t+3]
            colSisters = col[0:t] + col[t+3:]
            square = gameSquares[ix // 3 + t]
            squareSisters = []
            for c in range (0, 9, 3):
                squareSisters += square[c:c + (ix % 3)] + square[c + (ix % 3) + 1:c+3]
            gameTriplets += [ [ triplet, colSisters, squareSisters ] ]
            
    return gameNines, gameTriplets
    

# this will apply our reduction rules to the given grid state
# until we can't reduce it further.  debugLevel can be 0=silent,
# 1=summary, 2=detail, 3=debug, 4=trace.  Returns 1 if the final
# state is a valid solution, -1 if it's invalid/impossible,
# or 0 if it's still a work in progress.
#
def applyAndValidate(gameNines, gameTriplets, debugLevel=0):
    inlen = len([ x for x in pandas.core.common.flatten(gameNines[0:9]) ])
    done = False
    passes = 0

    # apply rules
    #
    while (not done):
        count = 0

        if (debugLevel >= 1):
            print("\nPass #" + str(passes := passes + 1) + " len=" + str(inlen))

        count += eliminateFound(gameNines, gameTriplets, debugLevel=debugLevel)
        count += uniqueCell(gameNines, gameTriplets, debugLevel=debugLevel)
        if (count == 0):
            count += nakedTuple(gameNines, gameTriplets, debugLevel=debugLevel)
        if (count == 0):
            count += hiddenTuple(gameNines, gameTriplets, debugLevel=debugLevel)
        if (count == 0):
            count += lockedCandidates(gameNines, gameTriplets, debugLevel=debugLevel)
        if (count == 0):
            count += xWing(gameNines, gameTriplets, debugLevel=debugLevel)
        if (count == 0):
            count += swordfish(gameNines, gameTriplets, debugLevel=debugLevel)

        newlen = len([ x for x in pandas.core.common.flatten(gameNines[0:9]) ])
        
        if (debugLevel >= 1):
            print("Done pass #" + str(passes) + 
                  " [" + str(count) + " cell(s)], in = " + str(inlen) + ", out = " + str(newlen))
            if (debugLevel >= 3):
                printGrid(gameNines[0:9], False)

        if (newlen < inlen):
            inlen = newlen
        else:
            done = True
    
    # is our grid complete or invalid?
    # invalid grids will contain at least one empty list
    # complete grids are valid grids of flat length 81
    #
    if (any([ len(cell) == 0 for row in gameNines[0:9] for cell in row ])):
        return -1
    
    if (inlen == 81):
        return 1
    
    return 0


# --------------- debugging and logging -----------------

# returns a string representing the given "nine", for logging
#
def nineName(i):
    return ["R", "C", "S"][i // 9] + str(i % 9)

    
# returns a string representing a triplet, for logging
#
def tripletName(i):
    out = ["R", "C"][i // 27]
    i = i % 27
    
    if (out == "R"):
        out += str(i // 3) + "S" + str((i // 9) * 3 + (i % 3))
    else:
        out += str(i // 3) + "S" + str((i // 9) + (i % 3) * 3)

    return out


# this prints a full game status including cell possibilities
# first printout is count per cell (withCounts=False suppresses)
# second is the actual game state
#
def printGrid(grid, withCounts=True):
    
    if (withCounts):
        print("[")
        for row in grid:
            print( "  " + str([ len(x) for x in row ]) )
        print("]\n")

    print("[")
    for row in grid:
        print("  " + str(row))
    print("]\n")

    
# this prints a simple version of the game status, without possibilities.
# 1:9 = found number
# X = cell is dead (invalid game)
# ? = dunno yet
#
def printSimpleGrid(game):
    print("[")
    for row in game[0:9]:
        print("  " + " ".join([ "X" if len(cell) == 0 else (str(list(cell)[0]) if len(cell) == 1 else "?") for cell in row ]))
    print("]\n")
    

# ------------------- Da Rules --------------------

# all rules take three arguments:  the gameNines, the gameTriplets, and
# a debug flag (0=silent, 1=summary, 2=detail, 3=debug, 4=trace).  All rules
# must return the number of cells reduced during the call.

# eliminateFound() : if in any ninesome (row, column, square) we have
# found the cell in which a number goes, remove it from all other cells.
#
def eliminateFound(nines, _, debugLevel=0):
    count = 0

    for ix, nine in enumerate(nines):
        nn = nineName(ix)
        lastCount = count
        
        for cell in nine:
            if (len(cell) == 1):
                others = [ c for c in nine if c is not cell and c & cell ]
                for c in others:
                    c -= cell
                    count += 1
                
        if ((debugLevel >= 2 and lastCount < count) or (debugLevel >= 4)):
            print ("o eliminateFound - {} reduced {} cell(s)".format(nn, count - lastCount))
            if (debugLevel >= 4 and lastCount < count):
                printGrid(nines[0:9])
            
    if (debugLevel >= 1):
        print("Rule eliminateFound complete - total of {} cell(s) reduced".format(count))
        
    return count


# uniqueCell() : if in any ninesome (row, column, square) a number is
# found in only one cell, eliminate all other numbers in that cell
#
def uniqueCell(nines, _, debugLevel=0):
    count = 0

    for ix, nine in enumerate(nines):
        nn = nineName(ix)
        lastCount = count

        for i in range(1, 10):
            foundIn = [ cell for cell in nine if i in cell ]
            if (len(foundIn) == 1 and len(foundIn[0]) > 1):
                foundIn[0] &= { i }
                count += 1

        if ((debugLevel >= 2 and lastCount < count) or (debugLevel >= 4)):
            print ("o uniqueCell - {} reduced {} cell(s)".format(nn, count - lastCount))
            if (debugLevel >= 4 and lastCount < count):
                printGrid(nines[0:9])

    if (debugLevel >= 1):
        print("Rule uniqueCell complete - total of {} cell(s) reduced".format(count))

    return count


# lockedCandidates(): if in any triplet (an intersection of a row/column
# with a square), a number appears in the triplet, then it must appear in
# both of its sister groups (same row/col but different square OR same
# square but different row/col) or neither.  In other words, either the
# number belongs in the triplet or it doesn't, and in the latter case,
# we still need to find a place for it elsewhere in its row/col AND in
# its square.  This is called a "locked candidates" rule in Sudoko.
#
# There are 54 such 'triplets' in the grid, and we conveniently
# pre-computed them when setting up the game.  The format of each
# triplet is [ [tripletCells], [lineSisters], [squareSisters] ]
#
def lockedCandidates(nines, triplets, debugLevel=0):
    count = 0
    
    for ix, trip in enumerate(triplets):
        inTriplet = { num for cell in [ c for c in trip[0] if len(c) > 1 ] for num in cell }
        inLine =  { num for cell in trip[1] for num in cell }
        inSquare =  { num for cell in trip[2] for num in cell }
        tn = tripletName(ix)
        lastCount = count
    
        for num in inTriplet:

            # triplet number is in the sister line, but not in the sister square.
            # ergo, it belongs in one of the three cells in the triplet.
            # remove all occurrences of it from the sister line.
            #
            if (num in inLine) and (not num in inSquare):
                for cell in trip[1]:
                    if (num in cell):
                        cell -= { num }
                        count += 1
            
            # vice versa - it's in the sister square but not the sister line
            #
            if (num in inSquare) and (not num in inLine):
                for cell in trip[2]:
                    if (num in cell):
                        cell -= { num }
                        count += 1
                        
        if ((debugLevel >= 2 and lastCount < count) or (debugLevel >= 4)):
            print ("o lockedCandidates - {} reduced {} cell(s)".format(tn, count - lastCount))
            if (debugLevel >= 4 and lastCount < count):
                printGrid(nines[0:9])

    if (debugLevel >= 1):
        print("Rule lockedCandidates complete - total of {} cell(s) reduced".format(count))

    return count


# xWing(): if number N only appears in cells (a, b) of row X, and N also appears only
# in cells (a, b) of row Y, then we can rule out N appearing in any other cell in
# column A and column B.  The same holds true when swapping columns and rows.  This
# is called an X-Wing Rule, though I kind of like Hashtag Rule better (because you are
# essentially creating a hashtag of two rows and two columns).

def xWing(nines, _, debugLevel=0):
    count = 0

    for i1, row1 in enumerate(nines[0:8]):
        for i2, row2 in enumerate(nines[i1 + 1:9], start=i1 + 1):
            count += xWing1(nines, row1, row2, nines[9:18], "R{}x{}".format(i1, i2), debugLevel)
    for i1, col1 in enumerate(nines[9:17]):
        for i2, col2 in enumerate(nines[i1 + 10:18], start=i1 + 1):
            count += xWing1(nines, col1, col2, nines[0:9], "C{}x{}".format(i1, i2), debugLevel)

    if (debugLevel >= 1):
        print("Rule xWing complete - total of {} cell(s) reduced".format(count))

    return count


def xWing1(nines, line1, line2, perps, pairName, debugLevel=0):
    count = 0
    wingPair = []

    for n in range(1, 10):
        l1 = [ ix for ix, cell in enumerate(line1) if n in cell ]
        l2 = [ ix for ix, cell in enumerate(line2) if n in cell ]
        
        if (len(l1) == 2 and l1 == l2):
            keep = [ line1[l1[0]], line1[l1[1]], line2[l1[0]], line2[l1[1]] ]
            for cell in perps[l1[0]] + perps[l1[1]]:
                if (n in cell) and not any(k for k in keep if k is cell):   # note: identity test, like JS ===
                    cell -= { n }
                    count += 1
                    wingPair = tuple(l1)

    if ((debugLevel >= 2 and count > 0) or (debugLevel >= 4)):
        print ("o xWing - {}:{} reduced {} cell(s)".format(pairName, wingPair, count))
        if (debugLevel >= 4 and count > 0):
            printGrid(nines[0:9])

    return count


# nakedTuple(): if in any nine, an n-tuple has (n-1) cells that are 
# subsets of it, then its numbers can be removed from all other cells
# in the nine.
#
def nakedTuple(nines, _, debugLevel=0):
    count = 0
    
    for ix, nine in enumerate(nines):
        nn = nineName(ix)
        lastCount = count

        for cell in nine:
            if (len(cell) > 1):
                isSubset = tuple(map(lambda c : cell >= c, nine))

                if (isSubset.count(True) == len(cell)):
                    toReduce = [ c for isSub, c in zip(isSubset, nine) if (not isSub) and c & cell ]
                    for c in toReduce:
                        c -= cell
                        count += 1
                        
        if ((debugLevel >= 2 and lastCount < count) or (debugLevel >= 4)):
            print ("o nakedTuple - {} reduced {} cell(s)".format(nn, count - lastCount))
            if (debugLevel >= 4 and lastCount < count):
                printGrid(nines[0:9])

    if (debugLevel >= 1):
        print("Rule nakedTuple complete - total of {} cell(s) reduced".format(count))

    return count


# hiddenTuple(): if in any nine, an n-tuple has (n-1) cells that are
# supersets of it, and its numbers appear in no other cell, then we
# can eliminate all other numbers in the superset cells.
#
def hiddenTuple(nines, _, debugLevel=0):
    count = 0
    
    for ix, nine in enumerate(nines):
        nn = nineName(ix)
        lastCount = count

        for cell in nine:
            if (len(cell) > 1):
                # 1 for superset, -1 for non-superset intersection, 0 for disjoint
                isIntersect = tuple(map(lambda c : 1 if cell <= c else (-1 if cell & c else 0), nine))

                if (isIntersect.count(True) == len(cell) and isIntersect.count(-1) == 0):
                    toReduce = [ c for isInter, c in zip(isIntersect, nine) if (isInter == 1) and len(c) > len(cell) ]
                    for c in toReduce:
                        c &= cell
                        count += 1
                        
        if ((debugLevel >= 2 and lastCount < count) or (debugLevel >= 4)):
            print ("o hiddenTuple - {} reduced {} cell(s)".format(nn, count - lastCount))
            if (debugLevel >= 4 and lastCount < count):
                printGrid(nines[0:9])

    if (debugLevel >= 1):
        print("Rule hiddenTuple complete - total of {} cell(s) reduced".format(count))

    return count


# swordfish(): This is a three-way X-wing, and it's also where I draw
# line for implementing more complex rules.  We'll do a search from
# here on out.

def swordfish(nines, _, debugLevel=0):
    count = 0

    for i1, row1 in enumerate(nines[0:7]):
        for i2, row2 in enumerate(nines[(i1+1):8], start=i1 + 1):
            for i3, row3 in enumerate(nines[(i2+1):9], start=i2 + 1):
                count += swordfish1(nines, row1, row2, row3, nines[9:18], "R{}x{}x{}".format(i1, i2, i3), debugLevel)
    for i1, col1 in enumerate(nines[9:16]):
        for i2, col2 in enumerate(nines[i1 + 10:17], start=i1 + 1):
            for i3, col3 in enumerate(nines[i2 + 10:18], start=i2 + 1):
                count += swordfish1(nines, col1, col2, col3, nines[0:9], "C{}x{}x{}".format(i1, i2, i3), debugLevel)

    if (debugLevel >= 1):
        print("Rule swordfish complete - total of {} cell(s) reduced".format(count))

    return count


def swordfish1(nines, line1, line2, line3, perps, trioName, debugLevel=0):
    count = 0
    wingTrio = []

    for n in range(1, 10):
        l1 = [ ix for ix, cell in enumerate(line1) if n in cell and len(cell) > 1 ]
        l2 = [ ix for ix, cell in enumerate(line2) if n in cell and len(cell) > 1 ]
        l3 = [ ix for ix, cell in enumerate(line3) if n in cell and len(cell) > 1 ]
        
        foundInPerps = list(set(l1) | set(l2) | set(l3))

        if (min(len(l1), len(l2), len(l3)) >= 2 and len(foundInPerps) == 3):
            keep = [ c for ix, c in enumerate(line1) if ix in foundInPerps ] \
                 + [ c for ix, c in enumerate(line2) if ix in foundInPerps ] \
                 + [ c for ix, c in enumerate(line3) if ix in foundInPerps ]

            for cell in perps[foundInPerps[0]] + perps[foundInPerps[1]] + perps[foundInPerps[2]]:
                if (n in cell) and not any(k for k in keep if k is cell):   # note: identity test, like JS ===
                    cell -= { n }
                    count += 1
                    wingTrio = tuple(foundInPerps + [[n]])

    if ((debugLevel >= 2 and count > 0) or (debugLevel >= 4)):
        print ("o swordfish - {}:{} reduced {} cell(s)".format(trioName, wingTrio, count))
        if (debugLevel >= 4 and count > 0):
            printGrid(nines[0:9])

    return count


# -----------------------------

puzzle = [
    [0, 0, 6, 1, 0, 0, 0, 0, 8], 
    [0, 8, 0, 0, 9, 0, 0, 3, 0], 
    [2, 0, 0, 0, 0, 5, 4, 0, 0], 
    [4, 0, 0, 0, 0, 1, 8, 0, 0], 
    [0, 3, 0, 0, 7, 0, 0, 4, 0], 
    [0, 0, 7, 9, 0, 0, 0, 0, 3], 
    [0, 0, 8, 4, 0, 0, 0, 0, 6], 
    [0, 2, 0, 0, 5, 0, 0, 8, 0], 
    [1, 0, 0, 0, 0, 2, 5, 0, 0]
]

printGrid(sudoku_solver(puzzle), False)