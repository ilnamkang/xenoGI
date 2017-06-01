import sys,os
sys.path.append(os.path.join(sys.path[0],'..'))
import parameters,genomes,trees,families,scores,islands,analysis

def islandsOfInterest():
    longIslands = islandsInStrainLongEnough(minGenes)
    longOnChrom = islandsOnChromosome(longIslands)
    longOnChromInRange,overlapList,totalBases,islandsList,validationRanges,islandsPerRangeLL,coveragePerRangeL = islandsInRange(longOnChrom)
    overlap = sum(overlapList)
    for rangeIndex in range(0,len(validationRanges)):
        print("Range:",validationRanges[rangeIndex])
        print("Coverage:",coveragePerRangeL[rangeIndex]/(validationRanges[rangeIndex][1]-validationRanges[rangeIndex][0]))
        print("Islands:",islandsPerRangeLL[rangeIndex])
        print("----")
    print("SUMMARY:")
    print("Ranges:",validationRanges)
    print("Number of Islands per range: ", islandsList)
    print("Percent overlap: ", overlap/totalBases)
    print("All islands per range:",islandsPerRangeLL)

def islandsInStrainLongEnough(minGenes):
    '''returns a list of the xenoGI islands that are longer than minLength'''
    #list of islands in strain, empty list of islands to return
    potentialIslands = islandsOnAllValidationNodes()
    returnIslands = []
    
    #for each island, check that it meets our criteria
    for island in potentialIslands:
        islandGenesInStrainL = analysis.getIslandGenesInStrain(island,strainNum,familyL)
        
        #check island has at least min genes, if so add to list of potential islands
        if len(islandGenesInStrainL)>=minGenes: returnIslands.append(island)
    return returnIslands
    
def islandsOnChromosome(potentialIslands):
    returnIslands = []
    #loop through each island,if an island is on the correct chromosome,
    #add it to our list of potential islands
    for island in potentialIslands:
        islandGenesInStrainL = analysis.getIslandGenesInStrain(island,strainNum,familyL)
        chromFound = geneInfoD[geneNames.numToName(islandGenesInStrainL[0])][3]
        if (chromFound == chrom): returnIslands.append(island)
    return returnIslands

def islandsInRange(potentialIslands):
    validationRanges, totalBases=readRanges()
    islandsPerRangeLL = [[]]*len(validationRanges)
    coveragePerRangeL = [0]*len(validationRanges)
    returnIslands = []  #holds islands that have any overlap
    overlapList=[] #holds the # of bp that overlap w/ a validation island for each island we check
    islandsList=[0]*len(validationRanges) #holds the number of xenoGI islands that overlap w/ each validation range
    nodesLL,uniqueStrains = nodesPerRange()
    
    for island in potentialIslands:
        #get the start and end position for the islands
        islandGenesInStrainL = analysis.getIslandGenesInStrain(island,strainNum,familyL)
        if analysis.getNeighborhoodGenes(strainNum,geneOrderT,islandGenesInStrainL,0) is not None:
            neighbGenesL,firstIslandGene,lastIslandGene=analysis.getNeighborhoodGenes(strainNum,geneOrderT,islandGenesInStrainL,0)
            startPos = min(int(geneInfoD[geneNames.numToName(firstIslandGene)][4]), int(geneInfoD[geneNames.numToName(firstIslandGene)][5]))
            endPos = max(int(geneInfoD[geneNames.numToName(lastIslandGene)][5]),int(geneInfoD[geneNames.numToName(lastIslandGene)][4]))
            islandNode = island.mrca

            #check that island is in validation range
            inRange,overlap,indices=islandInRange(validationRanges, startPos, endPos, islandNode, nodesLL)

            for index in range(0,len(indices)):
                if indices[index] is 1: islandsPerRangeLL[index]=islandsPerRangeLL[index]+[island.id]

            #update overlap list
            overlapList.append(sum(overlap))
            #update the islandsList so it reflects how many xenoGI islands are in each range
            islandsList=list(map(lambda x,y:x+y, islandsList, indices))
            coveragePerRangeL=list(map(lambda x,y:x+y, coveragePerRangeL, overlap))
            #add the island to the returnIslands list if it overlaps with any validation range
            if inRange:
                returnIslands.append(island)

    return returnIslands, overlapList, totalBases, islandsList,validationRanges,islandsPerRangeLL,coveragePerRangeL

def islandInRange(validationRanges, startPos, endPos, islandNode, nodesLL):
    '''returns true if the island overlaps with any 
    validation ranges and false otherwise'''
    overlap = [0]*len(validationRanges)
    indices = [0]*len(validationRanges)
    for index in range(0,len(validationRanges)):
        vRange=validationRanges[index]
        if (islandNode in nodesLL[index]):
            overlap[index]=min((vRange[1]-vRange[0]),max((endPos-vRange[0]),0))-min((vRange[1]-vRange[0]),max((startPos-vRange[0]),0))
        if overlap[index]>0: indices[index]=1
    if sum(overlap)>0: return True, overlap, indices
    return False, overlap, indices


def islandsOnAllValidationNodes():
    '''makes a list of all islands at the nodes of interest'''
    nodesLL,uniqueStrains = nodesPerRange()
    allIslands = []
    for strain in uniqueStrains:
        allIslands+=islandByNodeL[int(strainStr2NumD[strain])]
    return allIslands

def readRanges():
    '''Read a file with start end ranges separated by tabs, and return list of lists.'''
    totalBases = 0
    f=open(validationFile,'r')
    outLL = []
    while True:
        s=f.readline()
        if s == "":
            break
        L=[]
        for elem in s.split('\t')[1:3]:
            L.append(int(elem))
        totalBases += (L[1]-L[0])
        outLL.append(L)
    return outLL, totalBases

def nodesPerRange():
    '''read a tab-separated file where the 3rd element of each line
    contains the strains (separated by commas) expected for that validation range'''
    f=open(validationFile,'r')
    nodesLL = []
    uniqueStrains = []
    while True:
        s=f.readline()
        if s == "":
            break
        nodes = []
        for strain in s.split('\t')[0].split(','):
            nodes.append(int(strainStr2NumD[strain]))
            if strain not in uniqueStrains: uniqueStrains.append(strain)
        nodesLL.append(nodes)
    return nodesLL,uniqueStrains

if __name__ == "__main__":

    #loading parameters from command line that will be used below
    paramFN=sys.argv[1]
    paramD = parameters.loadParametersD(paramFN)
    strainStr = sys.argv[2]
    chrom = sys.argv[3]
    validationFile = sys.argv[4]
    minGenes = int(sys.argv[5])

    tree,strainStr2NumD,strainNum2StrD = trees.readTree(paramD['treeFN'])

    strainNum = strainStr2NumD[strainStr]

    #node = strainStr2NumD[strainStr]
    
    # load islands and genes
    islandByNodeL=islands.readIslands(paramD['islandOutFN'],tree,strainStr2NumD)

    geneNames = genomes.geneNames(paramD['geneOrderFN'],strainStr2NumD,strainNum2StrD)

    subtreeL=trees.createSubtreeL(tree)
    subtreeL.sort()
    
    geneOrderT=genomes.createGeneOrderTs(paramD['geneOrderFN'],geneNames,subtreeL,strainStr2NumD)

    familyL = families.readFamilies(paramD['familyFN'],tree,geneNames,strainStr2NumD)

    geneInfoD = genomes.readGeneInfoD(paramD['geneInfoFN'])

    islandsOfInterest()
