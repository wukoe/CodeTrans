# -*- coding: utf-8 -*-
"""
Created on Fri Apr  1 20:45:29 2016
@author: wb
transform matlab code to python code
"""
import sys

###### TEXT processing
# Change section of S (marked by idex) to rep
def strch(S,idx,rep):
    S=S[:idx[0]]+rep+S[idx[1]+1:]
    return S

# Separate string before a specified stop symbol.
def findstop(S,sym,startidx=None):
    if startidx==None:
        startidx=0
    idx=S.find(sym,startidx)
    if idx==-1:
        return (S[startidx:],idx)
    else:
        return (S[startidx:idx].strip(),idx)

# Separate variable name(字母开头，只包含字母数字) in following string.
# out: idx stop at last char of name
def sepname(S,startidx=None):
    if startidx==None:
        startidx=0

    Slen,k=len(S),startidx
    # find 1st name-like char (alphabet)
    while k<Slen:
        x=S[k]
        if x.isalpha() or x=='_':  # find alphabet char
            break
        k+=1
    if k>=Slen:
        return (None,Slen-1)

    # 但若第一位之前的字符也属于有效字符，意味当前字符为更大字符的一部分，因此无效
    if k==startidx:
        if k>0:
            tp=S[k-1]
            if tp.isalpha() or tp=='_' or tp.isdigit():
                return (None,startidx)

    # find the full name
    name=x; k+=1
    while k<Slen:
        x=S[k]
        if x.isalpha() or x=='_' or x.isdigit(): # find number or alphabet char
            name+=x
            k+=1
        else:
            break
    k-=1
    return (name,k)


###### Work horse!
def convert(code):
    # Status storage
    switchname=[]
    funcout=[] # output vars of function

    # Sep to line
    code=code.split('\n')
    lN=len(code)

    for li in range(lN):
        S=code[li]

        ### comment mark change
        S=S.replace('%','#')
        S=S.rstrip() # remove all white space at end
        if S and S[-1]==';':
            S=S[:-1]

        ts=S.lstrip()
        if ts=='' or ts[0]=='#':
            code[li]=S
            continue
        else:
            commentloc=S.find('#') # find location of comment, for later use

        ### Operator
        S=S.replace('^','**')
        S=S.replace('{','[')
        S=S.replace('}',']')

        ### x.abc -> x['abc']
        idx = S.find('.')
        while idx != -1:
            # Check if this is a number or struct form
            # First find the full name of expression
            name,tp=sepname(S,idx+1)
            # if do found a valid name (第二个条件是为保证name是紧贴'.'的)
            if name!=None and tp==idx+len(name):
                S=strch(S,(idx,tp),'[\''+name+'\']')

            # move to next
            idx=S.find('.',tp+1)


        ### Treat 'function' expression
        idx=S.find('function')

        # make sure 1.'function' is a separate word, 2.it is not in comment text
        if idx!=-1 and sepname(S,idx)[0]=='function' and (commentloc==-1 or idx<commentloc):
            stidx=idx
            (tp,idx)=findstop(S,'=',idx+9)
            if idx!=-1: # now idx at '='
                funcout.append(tp)
                (tx,idx)=findstop(S,')',idx+1)
            else:  # in case no output expression
                (tx,idx)=findstop(S,')',stidx+9)

            tx = 'def ' + tx + '):'
            S=strch(S,(stidx,idx),tx)

        ### Treat 'for' expression
        idx=S.find('for')
        # make sure 1.'for' is a separate word, 2.it is not in comment text
        if idx!=-1 and sepname(S,idx)[0]=='for' and (commentloc==-1 or idx<commentloc):
            stidx=idx
            (vname,idx)=findstop(S,'=',idx+4) # now idx located at '='
            (loopst,idx)=findstop(S,':',idx+1)
            if commentloc==-1:
                tp=idx+1
                idx=len(S)-1
                looped=S[tp:idx+1].strip()
            else:
                looped,idx=findstop(S,'#',idx+1)
                idx-=1

            # make loop start number -1
            if loopst.isdigit():
                loopst=int(loopst)-1
                loopst=str(loopst)
            if loopst=='0':
                tx = 'for '+ vname + ' in range(' + looped + '): '
            else:
                tx = 'for '+ vname + ' in range(' + loopst + ',' + looped + '): '
            S=strch(S,(stidx,idx),tx)

        ### Treat 'while' expression
        idx=S.find('while')
        if idx!=-1 and sepname(S,idx)[0]=='while' and (commentloc==-1 or idx<commentloc):
            if commentloc==-1: # append':' to end if no comment in line
                S+=':'
            else:
                idx=findstop(S,'#',idx+5)[1]
                S=strch(S,(idx,idx),': #')


        ### Treat 'if' expression
        idx=S.find('if')
        # make sure 1.'if' is a separate word, 2.it is not in comment text
        if idx!=-1 and sepname(S,idx)[0]=='if' and (commentloc==-1 or idx<commentloc):
            if commentloc==-1:
                S+=':'
            else:
                idx=findstop(S,'#',idx+2)[1]
                S=strch(S,(idx,idx),': #')

        idx=S.find('elseif')
        if idx!=-1 and sepname(S,idx)[0]=='elseif' and (commentloc==-1 or idx<commentloc):
            S=strch(S,(idx,idx+5),'elif')
            if commentloc==-1:
                S+=':'
            else:
                idx=findstop(S,'#',idx+6)[1]
                S=strch(S,(idx,idx),': #')

        idx=S.find('else')
        if idx!=-1 and sepname(S,idx)[0]=='else' and (commentloc==-1 or idx<commentloc):
            S=strch(S,(idx,idx+3),'else: ')

        ### Treat 'switch' expression
        idx=S.find('switch')
        if idx!=-1 and sepname(S,idx)[0]=='switch' and (commentloc==-1 or idx<commentloc):
            stidx=idx
            vname,idx=sepname(S,idx+6)
            switchname.append(vname)
            S=strch(S,(stidx,idx),'')

        idx=S.find('case')
        if idx!=-1 and sepname(S,idx)[0]=='case' and (commentloc==-1 or idx<commentloc):
            tex = 'elif ' + switchname[-1] + '=='
            S=strch(S,(idx,idx+3),tex)
            if commentloc==-1:
                S+=':'
            else:
                idx=findstop(S,'#',idx+2)[1]
                S=strch(S,(idx,idx),': #')

        idx=S.find('otherwise')
        if idx!=-1 and sepname(S,idx)[0]=='otherwise' and (commentloc==-1 or idx<commentloc):
            S=strch(S,(idx,idx+8),'else:')

        ### delete 'end'
        idx=S.find('end')
        # make sure 1.'end' is a separate word, 2.it is not in comment text
        if idx!=-1 and sepname(S,idx)[0]=='end' and (commentloc==-1 or idx<commentloc):
            S=strch(S,(idx,idx+2),'')

            # status update (end is finish of loop or structure)
            if switchname!=[]:
                switchname.pop()

        ### functions
        idx=S.find('zeros(')
        if idx!=-1:
            S=strch(S,(idx,idx+5),'np.zeros(')
        idx=S.find('ones(')
        if idx!=-1:
            S=strch(S,(idx,idx+4),'np.ones(')
        idx=S.find('rand(')
        if idx!=-1:
            S=strch(S,(idx,idx+4),'np.random.rand(')


        ''' More
        cell{} -> list []
        lambda express
        () -> []
        error
        isfiled
        '''
        ###
        code[li]=S

    if funcout!=[]:
        code.append('return '+funcout.pop()) #<<< one more: if multi functions ... need to apply multiple returns.

    return '\n'.join(code)


###### File handler
def ConvFile(fileIn,fileOut=None):
    # read file
    fname=fileIn.rsplit('.',1) # separate to name and postfix
    if fname[1]!='m':  # check file type to be matlab file
        tp=input('not matlab file, OK?[y/n]:')
        if tp!='y':
            print('convert terminated')
            return
    if not fileOut:
        fileOut=fname[0]+'.py'

    with open(fileIn,'r') as fh:
        S=fh.read()

    S=convert(S)

    with open(fileOut,'w',encoding='utf-8') as fh:
        fh.write(S)

    return


if __name__ == '__main__':
    fileIn=sys.argv[1]
    if len(sys.argv)==3:
        fileOut=sys.argv[2]
    else:
        fileOut=None

    ConvFile(fileIn,fileOut)

