#!/bin/sh
# paws.py = src/ parçalarının birleşimi (yardımcılar Bloop Bonkers motorundan). Düzenleme src/ içinde yapılır.
cd "$(dirname "$0")" && cat src/head.py src/helpers.py src/bg.py src/pets.py src/gags2.py src/gags3.py > paws.py && echo "" >> paws.py && cat src/audio.py src/tail.py >> paws.py
