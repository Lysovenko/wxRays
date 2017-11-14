#!/bin/bash
find .. -name \*.py | xargs xgettext -o wxRays.pot
msguniq  wxRays.pot -u -o wxRays.pot
NEWEST="$(ls -t *.po | head -n1)"
for i in *.po
do
    # update only manually modified po file
    if [ -f "${i}~" ]
    then
        msgmerge -U "$i" wxRays.pot
    fi
    fnam="../locale/${i%.po}/LC_MESSAGES/wxRays.mo"
    mkdir -p "../locale/${i%.po}/LC_MESSAGES"
    if [ "$i" -nt "$fnam" ] 
    then
        echo $fnam
        rm -f "$fnam"
        msgfmt "$i" -o "$fnam"
    fi
done


