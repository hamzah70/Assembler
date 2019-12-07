# CSE 112 : Computer Organization
# Project 1 : Assembler
# Made by : Hamzah Akhtar (2018051) and Shashwat Aggarwal (2018097)

import argparse
import re
import sys
from tabulate import tabulate

opCodes = {
    'CLA' : "0000",
    'LAC' : "0001",
    'STA' : "0010",
    'ADD' : "0011",
    'SUB' : "0100",
    'BRZ' : "0101",
    'BRN' : "0110",
    'BRP' : "0111",
    'INP' : "1000",
    'DSP' : "1001",
    'MUL' : "1010",
    'DIV' : "1011",
    'STP' : "1100",
    'DW' : "1101"
}

opcode_table = []            
opcode_offset = []
opcode_operand = []

literal_table  = []
literal_offset = []

symbol_table = []
symbol_offset = []

error_stack = []
warning_stack = []

finalOutput = []

instructionLocation = 0

startFound = False
endFound = False


def containsSpecialCharacters(string):
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    if(regex.search(string) == None):
        return False
    else:
        return True

def isLiteral(string):
    literal_regex = re.compile("^'=[0-9]+'$")
    if(literal_regex.search(string)!=None):
        return True
    else:
        return False

def isNotKeyWord(string):
    for key in opCodes:
        if(string==key):
            return False
    return True
          

def firstPass(inputFile):
    locationCounter = 0      
    global startFound
    global endFound  
    global instructionLocation
    
    with open(inputFile, 'r') as assemblyFile:
        for line in assemblyFile :
            
            stringLine = line
            line = line.strip('\n').split()

            line_length = len(line)

            if(endFound):
                warning_stack.append(["Unreachable code!", stringLine])
            
            if(line_length == 1):
                if(line[0] == "STP" or line[0] == "CLA"):
                    opcode_table.append(line[0]) 
                    opcode_operand.append("NONE")
                    opcode_offset.append(locationCounter)
                    locationCounter+=1
                elif(line[0] == "END"):
                    if(startFound):
                        endFound = True
                    else:
                        error_stack.append(["END found before start!!", stringLine])
                else:
                    if(line[0] in opCodes.keys()):
                        error_stack.append(["Missing operand!", stringLine])
                    else:
                        error_stack.append(["Invalid opcode!", stringLine])
                
            elif(line_length == 2):
                if(line[0] in opCodes.keys()):
                    opcode_table.append(line[0])
                    opcode_offset.append(locationCounter)

                    if(not containsSpecialCharacters(line[1])):
                        if(isNotKeyWord(line[1])):                       
                            opcode_operand.append(line[1])
                            if(isLiteral(line[1])):
                                literal = line[1][2:-1]
                                literal_table.append(literal)
                                literal_offset.append("NONE")
                            elif(not line[1].isdigit()):
                                if(line[1] not in symbol_table):
                                    symbol_table.append(line[1])
                                    symbol_offset.append("NONE")
                        else:
                            error_stack.append(["Syntax Error! Cannot use keyword as symbol!", stringLine])        
                    else:
                        error_stack.append(["Syntax Error! Invalid characters used!!",stringLine])
                elif(':' in line[0] and not containsSpecialCharacters(line[0].split(':')[0]) and isNotKeyWord(line[0].split(':')[0])):
                    # Check Label definition line
                    label = line[0].split(':')[0]
                    if(label not in symbol_table):
                        symbol_table.append(label)
                        symbol_offset.append(locationCounter)
                    else:
                        ind = symbol_table.index(label)
                        if(symbol_offset[ind]=="NONE"):
                            symbol_offset[ind] = locationCounter
                        else:
                            error_stack.append(["Symbol already declared!", stringLine])
                    if(line[1] == "STP" or line[1] == "CLA"):
                        opcode_table.append(line[1]) 
                        opcode_operand.append("NONE")
                        opcode_offset.append(locationCounter)
                    else:
                        if(line[1] in opCodes.keys()):
                            error_stack.append(["Insufficient operands!", stringLine])
                        else:
                            error_stack.append(["Invalid opcode!", stringLine])
                elif(line[0] == "START"):
                    if(locationCounter == 0):
                        if(line[1].isdigit()):
                            instructionLocation = int(line[1])
                            locationCounter = instructionLocation
                            startFound = True
                        else:
                            error_stack.append(["Invalid memory location!", stringLine])    
                    else:
                        if(startFound):
                            error_stack.append(["START already declared at top!", stringLine])
                        else:
                            error_stack.append(["START is not at top!!", stringLine])
                else:
                    error_stack.append(["Syntax error!", stringLine])
                        
                locationCounter += 1

            elif(line_length == 3 and ':' in line[0]):
                if(line[0].split(':')[0] not in symbol_table):
                    symbol_table.append(line[0].split(':')[0])
                    symbol_offset.append(locationCounter)
                elif(line[0].split(':')[0] in symbol_table):
                    ind = symbol_table.index(line[0].split(':')[0])
                    if(symbol_offset[ind]=="NONE"):
                        symbol_offset[ind] = locationCounter
                    else:
                        error_stack.append(["Symbol already declared!", stringLine])
                    
                if(line[1] in opCodes.keys()):
                    if(not containsSpecialCharacters(line[2])):
                        opcode_table.append(line[1])
                        opcode_operand.append(line[2])
                        opcode_offset.append(locationCounter)
                    else:
                        error_stack.append(["Syntax error! Invalid characters used!!", stringLine])
                else:
                    error_stack.append(["Invalid opcode!", stringLine])
                locationCounter+=1
            else:
                error_stack.append(["Syntax error!", stringLine])
                
        if("STP" not in  opcode_table):
            error_stack.append(["STP not found!", ""])
        for i in range(len(symbol_offset)):
            if(symbol_offset[i] == "NONE"):
                error_stack.append(["Symbol not defined", symbol_table[i]])
        if(not startFound):
            error_stack.append(["START not found!", "START xxx"])
        if(not endFound):
            error_stack.append(["END not found!", "END"])

    for i in range(len(literal_table)):
        literal_offset[i] = locationCounter
        locationCounter+=1



def second_pass(inputFile):
    locationCounter = instructionLocation
    with open(inputFile, 'r') as assemblyFile:

        for line in assemblyFile:
            output = []
            binary_location_counter = format(locationCounter, '08b')

            line = line.strip('\n').split()

            if(line[0] != "END" and line[0] != "START"):
                output.append(binary_location_counter)

                if(len(line) == 1):
                    if(line[0] in opCodes.keys()):
                        output.append(opCodes[line[0]])
                        output.append(format(0,'08b'))

                elif(len(line) == 2):
                    if(line[0] in opCodes.keys()):
                        output.append(opCodes[line[0]])

                        if(line[1].isdigit()):
                            output.append(format(int(line[1]), '08b'))

                        elif(line[1] in symbol_table):
                            ind = symbol_table.index(line[1])
                            offset = symbol_offset[ind]
                            output.append(format(offset,'08b'))

                        elif('=' in line[1]):
                            literal = line[1][2:-1]
                            ind = literal_table.index(literal)
                            offset = literal_offset[ind]
                            output.append(format(offset,'08b'))

                    elif(line[1] in opCodes.keys()):
                        output.append(opCodes[line[1]])
                        output.append(format(0,'08b'))

                elif(len(line) == 3):
                    if(line[1] in opCodes.keys()):
                        output.append(opCodes[line[1]])
                        if(line[2].isdigit()):
                            output.append(format(int(line[2]),'08b'))

                        elif(line[2] in symbol_table):
                            ind = symbol_table.index(line[2])
                            offset = symbol_offset[ind]
                            output.append(format(offset,'08b'))

                        elif('=' in line[2]):
                            literal = line[2][2:-1]
                            ind = literal_table.index(literal)
                            offset = literal_offset[ind]
                            output.append(format(offset,'08b'))

                finalOutput.append(output)
                locationCounter+=1

def fileOutput():
    with open("MachineCode.txt",'w') as f:
        f.write(tabulate(finalOutput))
        f.close()

def opcodeTableOutput():
    with open("OpcodeTable.txt", 'w') as f:
        f.write(tabulate(list(zip(opcode_table,opcode_operand,opcode_offset)),headers=["OPCODE","OPERAND","OFFSET"]))
        f.close()

def symbolTableOutput():
    with open("SymbolTable.txt", 'w') as f:
        f.write(tabulate(list(zip(symbol_table, symbol_offset)),headers=["SYMBOL","OFFSET"]))
        f.close()

def literalTableOutput():
    with open("LiteralTable.txt", 'w') as f:
        f.write(tabulate(list(zip(literal_table,literal_offset)),headers=["LITERAL","OFFSET"]))
        f.close()

def fileCreation():
    fileOutput()
    opcodeTableOutput()
    symbolTableOutput()
    literalTableOutput()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert input assembly language code into machine language code.")
    parser.add_argument("inputFile", help='Name of the input file', type=str)
    args = parser.parse_args()
    firstPass(args.inputFile)
    
    if not error_stack:    
        print('\n' + tabulate(list(zip(opcode_table,opcode_operand,opcode_offset)),headers=["Opcode","Operands","Offset"])+'\n')
        print(tabulate(list(zip(symbol_table, symbol_offset)),headers=["Symbol","Offset"])+'\n')
        print(tabulate(list(zip(literal_table,literal_offset)),headers=["Literal","Offset"])+'\n')
        if warning_stack:
            print(tabulate(warning_stack, headers=["Warning message", "Warning line"])+'\n')

        second_pass(args.inputFile)   
        fileCreation()

        print("MACHINE CODE")
        print(tabulate(finalOutput))             
    else:
        print(tabulate(error_stack, headers=["Error message", "Error Line"])+'\n')
        if warning_stack:
            print(tabulate(warning_stack, headers=["Warning message", "Warning line"])+'\n')
