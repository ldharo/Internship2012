#!/bin/sh

for toTranslate in `ls interp*.py | sort`
do
    RPtranslateJIT $toTranslate
done

for toRun in `ls *-c | sort`
do
    PYPYLOG=jit-log-opt:out ./$toRun ../benchmarks/test10runs100000
    export newName="out-$toRun"
    mv out $newName
    rm out
done