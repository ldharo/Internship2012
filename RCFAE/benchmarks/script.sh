#!/bin/sh

# Start by cleaning out the repertory
rm out* *.pyc *-c test* result*

# Create translated, non JITing version of the interpreters
export filToTranslate=""

for fileName in "interpretIter" "interpretTramp"
do
    fileToTranslate="$fileName.py"
    RPtranslate $fileToTranslate
    export toRename="$fileName-c"
    export newName="RP$toRename"
    mv $toRename $newName
done

# Create translated, JITing version of the interpreters

for fileName in "interpretIter" "interpretTramp"
do
    fileToTranslate="$fileName.py"
    RPtranslateJIT $fileToTranslate
    export toRename="$fileName-c"
    export newName="RPJIT$toRename"
    mv $toRename $newName
done

# Test production

export nodes=6
export runs=1000

export max_nodes=10
export max_runs=100000

until [ "$nodes" -gt "$max_nodes" ];
do
    until [ "$runs" -gt "$max_runs" ];
    do
    	pypy ./writeProg.py $nodes $runs
    	runs=`expr $runs \\* 10`
    done
    nodes=`expr $nodes + 2`
    runs=1000
done


# Run tests

export i=0
export max_tests=10

export fileToWrite=''

export security=0

for fileToRun in `ls RP* | sort`
do
    fileToWrite="result-$fileToRun-0"
    echo "Tests of $fileToRun\n">>$fileToWrite
    for fileToTest in `ls test* | sort`
    do
	echo "Testing $fileToTest\n" >>$fileToWrite
	until [ "$i" -gt $max_tests ];
	do
	    echo "run $i" >> $fileToWrite
	    /usr/bin/time ./$fileToRun $fileToTest 2>> $fileToWrite
	    security=`echo $?`
	    echo "" >> $fileToWrite
	    if [ "$security" -ne 0 ]; 
	    then
		echo "Abort tests of $fileToTest">>$fileToWrite
		i=`expr $max_tests + 1`
	    else
		i=`expr $i + 1`
	    fi
	done
	i=0
    done
done

# Verify if a trace is produced or not

for fileToRun in `ls RPJIT* | sort `
do
    for fileToTest in `ls test* | sort`
    do
	fileToWrite="out-$fileToRun"
	echo "Trace $fileToTest" >> $fileToWrite
	echo "" >> $fileToWrite
	PYPYLOG=jit-log-opt:out ./$fileToRun $fileToTest
	echo "" >> $fileToWrite
	cat <out >>$fileToWrite
	rm out
    done
done