import os
import laspy
import subprocess
import scipy.io as sio
import numpy as np
from datetime import datetime


'''
This script generates, from the NGS tiles, the input tiles for
"calc_aerial_TPU.py".  This script does 4 main things (using the 
subprocess package to call 4 unlicensed lastools executables):

1)  LAS2LAS.EXE:    extract the bathy (las class code 26) from the 
                    NGS-provided tiles
                    
2)  LASSORT.EXE:    sort the bathy-only tiles by gps-time (which is 
                    required by the merge process in the TPU code)
                    
3)  LASSPLIT.EXE:   split the time-sorted bathy-only tiles into individual 
                    flight-line tiles (the polynomial surface process in 
                    the TPU code behaves better when working with individual 
                    flight lines)
                    
4)  LASTILE.EXE:    subtiles any NGS-provided tile that has too many data 
                    points (some of the unlicensed lastools have limits)
'''


def run_console_cmd(cmd):
    process = subprocess.Popen(cmd.split(' '))
    output, error = process.communicate()
    returncode = process.poll()

    return returncode, output


def get_num_points(las):

    inFile = laspy.file.File(las, mode="r")
    num_file_points = inFile.__len__()

    return num_file_points


def get_las_files(las_dir, contains):
    las_files = ['\\'.join([las_dir, f])
                 for f in os.listdir(las_dir)
                 if contains in f]

    return las_files


def las2las(i, las, las_tools_dir):
    las_short_name = las.split('\\')[-1]
    print('extracting class code {} ({}) from {} ({} of {})...'.format(
        classes[class_to_extract], class_to_extract, las_short_name, i+1, len(las_tiles)))
    las2las_path = r'{}\las2las'.format(las_tools_dir)
    out_las = '\\'.join([bathy_dir, las_short_name.replace('.las', '_BATHY.las')])
    las2las_cmd = r'{} -i {} -keep_classification {} -o {}'.format(
        las2las_path, las, classes['bathymetry'], out_las)
    returncode, output = run_console_cmd(las2las_cmd)


def lassort(i, las, total_num_las, las_tools_dir):
    las_short_name = las.split('\\')[-1]
    print('sorting {} by gps_time ({} of {})...'.format(
        las_short_name, i, total_num_las))
    lassort_path = r'{}\lassort'.format(las_tools_dir)
    out_las = '\\'.join([sorted_dir, las_short_name.replace('BATHY', 'SORTED')])
    lassort_cmd = r'{} -i {} -gps_time -o {}'.format(lassort_path, las, out_las)
    returncode, output = run_console_cmd(lassort_cmd)


def lassplit(i, las, total_num_las, las_tools_dir, preprocess_dir):
    las_short_name = las.split('\\')[-1]
    print('splitting {} into flight lines ({} of {})...'.format(
        las_short_name, i, total_num_las))
    lassplit_path = r'{}\lassplit'.format(las_tools_dir)
    lassplit_cmd = r'{} -i {} -odir {} -olas'.format(
        lassplit_path, las, preprocess_dir)
    returncode, output = run_console_cmd(lassplit_cmd)


def lastile(las, out_dir, las_tools_dir):
    las_short_name = las.split('\\')[-1]
    print('tiling {} into {}-m tiles...'.format(
        las_short_name, tile_size))
    lastile_path = r'{}\lastile'.format(las_tools_dir)
    lastile_cmd = r'{} -i {} -o {} -tile_size {} -odir {} -olas'.format(
        lastile_path, las, las, tile_size, out_dir)
    returncode, output = run_console_cmd(lastile_cmd)


def main(las_tools_dir, las_dir, preprocess_dir):
    # FIXME:  These variables shouldn't be made global - done by Tim
    global processing_info
    processing_info = object()
    global classes, class_to_extract, bathy_dir, sorted_dir, tile_size, las_tiles
    
    tic = datetime.now()

    bathy_dir = '\\'.join([las_dir, 'TEMP\BATHY'])
    sorted_dir = '\\'.join([las_dir, 'TEMP\SORTED'])

    tile_size = 250
    class_to_extract = 'bathymetry'
    lassort_max_num_pts = 8e6
    lassplit_max_num_pts = 7.5e6
    classes = {'bathymetry': 26, }

    if os.path.exists(bathy_dir):  # dir for extracted bathy las files
        for fName in os.listdir(bathy_dir):
            os.remove(os.path.join(bathy_dir, fName))
    else:
        print('making {} dir...'.format(bathy_dir))
        os.makedirs(bathy_dir)
    
    if os.path.exists(sorted_dir):  # dir for time-sorted bathy files
        for fName in os.listdir(sorted_dir):
            os.remove(os.path.join(sorted_dir, fName))
    else:
        print('making {} dir...'.format(sorted_dir))
        os.makedirs(sorted_dir)
    
    if os.path.exists(preprocess_dir):  # dir for individual flight-line time-sorted bathy files
        for fName in os.listdir(preprocess_dir):
            os.remove(os.path.join(preprocess_dir, fName))
    else:
        print('making {} dir...'.format(preprocess_dir))
        os.makedirs(preprocess_dir)
    
    ###########################################################
    ###########################################################
    # run las2las.exe to extract bathy points (class code 26)
    tic_las2las = datetime.now()
    las_tiles = get_las_files(las_dir, contains='.las')
    for i, las in enumerate(sorted(las_tiles)):
        las2las(i, las, las_tools_dir)
    toc_las2las = datetime.now()
    las2las_time = toc_las2las - tic_las2las
    print('las2las completion time:  {}'.format(las2las_time))

    ###########################################################
    ###########################################################
    # run lassort to sort the bathy-only tiles by gps_time
    tic_lassort = datetime.now()
    las_tiles = get_las_files(bathy_dir, contains='BATHY')
    bathy_too_big = []
    total_num_las = len(las_tiles)  # can grow if any bathy tiles need to be tiled
    curr_ind = 0
    for las_bathy in sorted(las_tiles):

        las_bathy_base = las_bathy.split('\\')[-1][:-4]
        num_pts = get_num_points(las_bathy)

        if num_pts >= lassort_max_num_pts:

            print('{} has too many points ({})...'.format(las_bathy_base, num_pts))
            bathy_too_big.append(las_bathy)
            lastile(las_bathy, bathy_dir, las_tools_dir)

            # lassort newly tiled, smaller tiles
            # first, get list of new tiles with basename of original las
            print('sorting newly tiled, smaller bathy tiles...')
            smaller_bathy_tiles = ['\\'.join([bathy_dir, t])
                             for t in os.listdir(bathy_dir)
                             if las_bathy_base in t
                             and '\\'.join([bathy_dir, t]) != las_bathy]
            total_num_las += len(smaller_bathy_tiles) - 1  # -1 to exclude too-big file
            for z, t in enumerate(sorted(smaller_bathy_tiles)):
                print z
                curr_ind += 1
                lassort(curr_ind, t, total_num_las, las_tools_dir)  # show updated index and total # of las files

        else:
            curr_ind += 1
            lassort(curr_ind, las_bathy, total_num_las, las_tools_dir)

    bathy_too_big_file = open('{}\\bathy_too_big.txt'.format(bathy_dir), 'w')
    for las_bathy in bathy_too_big:
        bathy_too_big_file.write('{}\n'.format(las_bathy))
    bathy_too_big_file.close()

    toc_lassort = datetime.now()
    lassort_time = toc_lassort - tic_lassort
    print('lassort completion time:  {}'.format(lassort_time))

    ###########################################################
    ###########################################################
    # run lassplit to split sorted tiles into flightlines
    tic_lassplit = datetime.now()
    las_tiles = get_las_files(sorted_dir, contains='SORTED')
    sorted_too_big = []
    total_num_las = len(las_tiles)  # can grow if any bathy tiles need to be tiled
    curr_ind = 0
    for las_sorted in sorted(las_tiles):

        las_sorted_base = las_sorted.split('\\')[-1][:-4]
        num_pts = get_num_points(las_sorted)

        if num_pts >= lassplit_max_num_pts:

            print('{} has too many points ({})...'.format(las_sorted_base, num_pts))
            sorted_too_big.append(las_sorted)
            lastile(las_sorted, sorted_dir, las_tools_dir)

            # lasplit newly tiled, smaller tiles
            # first, get list of new tiles with basename of original las
            print('splitting newly tiled, smaller sorted tiles...')
            smaller_sorted_tiles = ['\\'.join([sorted_dir, t])
                                    for t in os.listdir(sorted_dir)
                                    if las_sorted_base in t
                                    and '\\'.join([sorted_dir, t]) != las_sorted]

            total_num_las += len(smaller_sorted_tiles) - 1  # -1 to exclude too-big file
            for t in sorted(smaller_sorted_tiles):
                curr_ind += 1
                lassplit(
                    curr_ind,
                    t,
                    total_num_las,
                    las_tools_dir,
                    preprocess_dir)

        else:
            curr_ind += 1
            lassplit(
                curr_ind,
                las_sorted,
                total_num_las,
                las_tools_dir,
                preprocess_dir)

    sorted_too_big_file = open('{}\\sorted_too_big.txt'.format(sorted_dir), 'w')
    for las_bathy in sorted_too_big:
        sorted_too_big_file.write('{}\n'.format(las_bathy))
    sorted_too_big_file.close()

    toc_lassplit = datetime.now()
    lassplit_time = toc_lassplit - tic_lassplit
    print('lassplit completion time:  {}'.format(lassplit_time))

    ###########################################################
    ###########################################################
    # output time summary
    print('-' * 50)
    print('las2las completion time:  {}'.format(las2las_time))
    print('lassort completion time:  {}'.format(lassort_time))
    print('lassplit completion time:  {}'.format(lassplit_time))
    print('TOTAL COMPLETION TIME:  {}'.format(datetime.now() - tic))

if __name__ == '__main__':
    main()