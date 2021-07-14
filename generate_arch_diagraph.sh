#!/bin/bash

pulumi stack graph architecture.dot
cat architecture.dot | \
    sed 's/{/{\n    overlap=scale;\nnode [shape=record];\n/' | \
    sed 's/urn:pulumi:dev::aisr-data-warehouse:://g' > tmp.dot
mv tmp.dot architecture.dot
neato -Tsvg -oarchitecture.svg architecture.dot