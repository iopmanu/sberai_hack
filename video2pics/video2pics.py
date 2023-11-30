import cv2
import os
import pathlib
import shutil

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
# input_dir = PROJECT_ROOT / "./video/"
# output_dir = PROJECT_ROOT / "./output_pics/"
TIME_SKIPS = float(1000) # 1000 - 1 second
MAX_SECONDS = 60


def video2frames(video_fname, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)
    vidcap = cv2.VideoCapture(video_fname)
    count = 0
    while vidcap.isOpened() and count < MAX_SECONDS:
        vidcap.set(cv2.CAP_PROP_POS_MSEC, (count * TIME_SKIPS))
        sucess, image = vidcap.read()
        if sucess:
            cv2.imwrite(os.path.join(output_dir, '%d.png') % count, image)
            count += 1
        else:
            break
    cv2.destroyAllWindows()
    vidcap.release()
