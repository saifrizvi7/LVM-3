import unittest
import threading
import cli
from test import support
import time
from runner import execute,fio
import subprocess

class Task(unittest.TestCase):
    disk = " ".join(cli.disk_name)

    def xlvcreate(self):
        print("Creating Physical Volume, Volume Group, Logical Volume, Creating Filesystem, Directory and mounting it")
        execute("pvcreate {}" .format(Task.disk))
        execute("vgcreate {} {}" .format(cli.vgname, Task.disk))
        execute("lvcreate --size {} --name {} {}".format(cli.size,cli.lvname,cli.vgname))
        
        self.lvpath = "/dev/{}/{}" .format(cli.vgname, cli.lvname)
        
        execute("sudo mkfs -t {} {}" .format(cli.fs, self.lvpath))
        execute("mkdir /data")
        execute("mount {} /data" .format(self.lvpath))
        self.fio_fun = fio("fio --filename={} --direct=1 --size=1G --rw=randrw --bs=4k --ioengine=libaio --iodepth=256 --runtime=5 --numjobs=32 --time_based --group_reporting --name=iops-test-job --allow_mounted_write=1".format(self.lvpath))
        self.fspath = "dev/mapper/{}-{}" .format(cli.vgname, cli.lvname)
        self.outpv = execute("pvdisplay")
        self.outvg = execute("vgdisplay")
        self.output = execute("lvdisplay")
        self.outmnt = execute("findmnt")
        
        for i in Task.disk:
            self.assertIn(i,self.outpv)
        self.assertIn(cli.vgname,self.outvg)
        self.assertIn(cli.lvname, self.output)
        self.assertIn(self.fspath,self.outmnt)
        self.assertIn("Run status",self.fio_fun)

    def tearDownClass(cls):
        #destroying pv ater running the test
        disk = " ".join(cli.disk_name)
        print("\nUnmounting /data directory, Removing /data Directory, removing the filesystem from the Logical Volume, \nRemoving the Logical Volume, Volume Group, Physical Volume")
        vgpath = "/dev/{}/{}".format(cli.vgname,cli.lvname)
        print("\nUnmounting /data directory")
        execute("rmdir /data")
        execute("wipefs -a {}".format(vgpath))
        execute("lvremove -f {}" .format(cli.vgname), inp="y\n")
        execute("vgremove {}".format(cli.vgname))
        execute("pvremove {}" .format(disk))


    def hread(self):
        time.sleep(3)
        execute("pvmove {}".format(cli.dtr))
        execute("vgreduce {0} {1}" .format(cli.vgname,cli.dtr))
        self.out = execute("pvdisplay -C -o pv_name,vg_name -S vgname={}".format(cli.vgname))
        self.assertNotIn(cli.dtr,self.out)
        print("vgreduced")


    def test_th(self):
        with support.catch_threading_exception() as cm:
            t1=threading.Thread(target=self.xlvcreate)
            t2=threading.Thread(target=self.hread)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            if cm.exc_value is not None:
                raise cm.exc_value

            

