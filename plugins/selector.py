from info import VIDS, PICS, CHPV

ML = None
if CHPV == 'vid':
    ML = VIDS
else:
    ML = PICS

MS = random.choice(ML)