import datetime
import os

# create files and rename history file in a dir
def h_create_rename_files(dirpath, hf_root, unchanging:list[str], num_files=3):

    # open a history file with header
    now = datetime.datetime.now()
    now_str = now.strftime("%Y_%m_%d_%H_%M_%S")
    hfilename = hf_root + '_'+ now_str +'.csv'
    histfile_obj=open(os.path.join(dirpath,hfilename), 'a')
    histfile_obj.write('from, to, %s\n' % now_str)
    # create/close some files 'A_<random>', 'A_<random>',...,
    # adding each with old_name 'A_<random>_old' ... to the history
    for fid in range (0, num_files):
        fname='A_'+str(fid)+'_old.jpg'
        tname='A_'+str(fid)+'.jpg'
        f=open(os.path.join(dirpath,tname),'a')
        f.close()
        histfile_obj.write(fname+','+tname+'\n')
    # close the history file
    histfile_obj.close()
    # add some files that should not be renamed
    for uf in unchanging:
        ncf=open(os.path.join(dirpath,uf), 'w')
        ncf.close()