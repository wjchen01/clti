import sys
from PIL import Image
from pathlib import Path

path = Path(sys.argv[1])

i = 0

for pfile in path.glob('**/*.jpg'):
    im = Image.open(pfile)
    print ("\t".join([pfile.name, str(im.size[0])]))
    im.close()
