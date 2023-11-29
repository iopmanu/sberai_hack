import cv2
import os
import pathlib
import shutil

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "./video/"
OUTPUT_DIR = PROJECT_ROOT / "./output_pics/"
TIME_SKIPS = float(1000) # 1000 - 1 second


def video2frames(filename):
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.mkdir(OUTPUT_DIR)
    vidcap = cv2.VideoCapture(str(INPUT_DIR) + f'/{str(filename)}')
    count = 0
    while vidcap.isOpened():
        vidcap.set(cv2.CAP_PROP_POS_MSEC, (count * TIME_SKIPS))
        sucess, image = vidcap.read()
        if sucess:
            cv2.imwrite(os.path.join(OUTPUT_DIR, '%d.png') % count, image)
            count += 1
        else:
            break
    cv2.destroyAllWindows()
    vidcap.release()
