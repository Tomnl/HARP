#!/usr/bin/python
# Import PyQT module
from PyQt4 import QtCore, QtGui
# Import MainWindow class from QT Designer
from MainWindow import Ui_MainWindow
from Run_processing import Progress
import zproject
import crop
import tempfile
#from RunProcessing import *
import sys
import subprocess
import os, signal
import re
# cPickle is faster than pickel and is pretty much the same
import pickle
import pprint
import time
import shutil
import uuid
import logging
from multiprocessing import freeze_support
try:
    import Image
except ImportError:
    from PIL import Image

class MainWindow(QtGui.QMainWindow):
    '''
    Class to provide the main window for the Image processing GUI.
    Basically extend the QMainWindow class (from MainWindow.py) generated by QT Designer

    Also shows a dialog box after a submission the dialog box will then keep a track of the
    image processing (not yet developed).
    '''

    def __init__(self, app):
       '''  Constructor: Checks for buttons which have been pressed and responds accordingly. '''

       # Standard setup of class from qt designer Ui class
       super(MainWindow, self).__init__()
       self.ui=Ui_MainWindow()
       self.ui.setupUi(self)
       self.app = app

       # Make unique ID if this is the first time mainwindow has been called
       self.unique_ID = uuid.uuid1()

       # Initialise various switches
       self.modality = "Not_selected"
       self.selected = "Not_selected"
       self.error = "None"
       self.stop = None
       self.processGoSwitch = "no"

       # initialise non essential information
       self.scan_folder = ""
       self.recon_log_path = ""
       self.f_size_out_gb = ""
       self.pixel_size = ""

       # Temp folder for pre-processing log and z-project
       self.tmp_dir = tempfile.mkdtemp()

       # First log file
       tmp_log = os.path.join(self.tmp_dir,"session.log")
       logging.basicConfig(filename=tmp_log,level=logging.DEBUG,format='%(asctime)s %(message)s')
       logging.info("########################################")
       logging.info("### HARP Session Log                 ###")
       logging.info("########################################")

       logging.info("ID for session:"+str(self.unique_ID))
       logging.info("Temp directory:"+self.tmp_dir)


       # get input folder
       self.ui.pushButtonInput.clicked.connect(self.selectFileIn)

       # Get output folder
       self.ui.pushButtonOutput.clicked.connect(self.selectFileOut)

       # OPT selection
       self.ui.radioButtonOPT.clicked.connect(self.getOPTonly)

       # uCT selection
       self.ui.radioButtonuCT.clicked.connect(self.getuCTonly)

       # If Go button is pressed move onto track progress dialog box
       self.ui.pushButtonGo.clicked.connect(self.processGo)

       # Set cropping options
       # Auto crop (disable buttons)
       self.ui.radioButtonAuto.clicked.connect(self.manCropOff)
       # No crop (disable buttons)
       self.ui.radioButtonNo.clicked.connect(self.manCropOff)
       # Man crop (enable buttons).
       self.ui.radioButtonMan.clicked.connect(self.manCropOn)
       # If the get dimensions button is pressed
       self.ui.pushButtonGetDimensions.clicked.connect(self.getDimensions)

       #Get the output folder name when input updated
       self.ui.lineEditOutput.textChanged.connect(self.outputFolderChanged)
       self.ui.lineEditInput.textChanged.connect(self.inputFolderChanged)

       # Get recon file manually
       self.ui.pushButtonCTRecon.clicked.connect(self.getReconMan)

       # Get scan file manually
       self.ui.pushButtonScan.clicked.connect(self.getScanMan)

       # Get SPR file manually
       self.ui.pushButtonCTSPR.clicked.connect(self.getSPRMan)

       # Update name
       self.ui.pushButtonUpdate.clicked.connect(self.updateName)

       # Get scan file manually
       self.ui.checkBoxPixel.clicked.connect(self.scaleByPixelOn)

       # Resize for smaller monitors
       self.ui.actionResize.triggered.connect(self.resizeScreen)

       # Reset screen size to standard
       self.ui.actionReset_screen_size.triggered.connect(self.resetScreen)

       # to make the window visible
       self.show()

    def resizeScreen(self):
        self.resize(1300,700)
        self.ui.scrollArea.setFixedSize(1241,600)

    def resetScreen(self):
        self.resize(1300, 1007)
        self.ui.scrollArea.setFixedSize(1241,951)


    def selectFileOut(self):
        ''' Select output folder (this should be blocked as standard'''
        self.fileDialog = QtGui.QFileDialog(self)
        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")
        if not folder == "":
            self.ui.lineEditOutput.setText(folder)

    def selectFileIn(self):
        ''' Get the info for the selected file'''
        self.fileDialog = QtGui.QFileDialog(self)
        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")

        if not folder == "":
            # Reset the inputs incase this is not the first time someone has selected a file
            self.resetInputs()

            # Set the input folder
            self.ui.lineEditInput.setText(folder)

            # Autocomplete the name
            self.getName()

            # Get the reconLog and associated pixel size
            self.getReconLog()

            # Get the output folder location
            self.autoFileOut()

            # Automatically identify scan folder
            self.autoGetScan()

            # Automatically get SPR file
            self.autoGetSPR()

            # Determine size of input folder
            self.folderSizeApprox()

    def resetInputs(self):
        self.ui.lineEditDate.setText("")
        self.ui.lineEditGroup.setText("")
        self.ui.lineEditAge.setText("")
        self.ui.lineEditLitter.setText("")
        self.ui.lineEditZygosity.setText("")
        self.ui.lineEditSex.setText("")
        self.ui.lineEditName.setText("")
        self.ui.lineEditCTRecon.setText("")
        self.ui.lineEditCTSPR.setText("")
        self.ui.lineEditScan.setText("")
        self.ui.lineEditOutput.setText("")
        self.ui.lcdNumberFile.display(0.0)
        self.ui.lcdNumberPixel.display(0.0)

    def getName(self):
        '''
        Gets the id from the folder name. Then fills out the text boxes on the main window with the relevant information
        '''
        # Get input folder
        input = str(self.ui.lineEditInput.text())

        # Get the folder name
        path,folder_name = os.path.split(input)


        # Need to have exception to catch if the name is not in correct format.
        # If the name is not in the correc format it should flag to the user that this needs to be sorted
        name_list = folder_name.split("_")

        self.ui.lineEditName.setText(folder_name)
        self.full_name = folder_name
        # Could put additional regexes to check format is correct but could be a little bit annoying for the user
        try:
            self.ui.lineEditDate.setText(name_list[0])
            self.ui.lineEditGroup.setText(name_list[1])
            self.ui.lineEditAge.setText(name_list[2])
            self.ui.lineEditLitter.setText(name_list[3])
            self.ui.lineEditZygosity.setText(name_list[4])
            self.ui.lineEditSex.setText(name_list[5])

        except IndexError as e:
            pass
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Name ID is not in the correct format\n')
            self.full_name = folder_name
        except:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Auto-populate not possible. Unexpected error:',sys.exc_info()[0])


    def getReconLog(self):
        '''
        Gets the recon log from the original recon folder and gets the pixel size information

        Updates the following qt objects: ... ...   ...

        Creates ...
        '''

        input = str(self.ui.lineEditInput.text())

        # Get the folder name
        path,folder_name = os.path.split(input)

        try:
            # This will change depending on the location of the program (e.g linux/windows and what drive the MicroCT folder is set to)
            recon_log_path = os.path.join(path,folder_name,folder_name+".txt")
            if os.path.exists(os.path.join(path,folder_name,folder_name+".txt")):
                recon_log_path = os.path.join(path,folder_name,folder_name+".txt")
            elif os.path.exists(os.path.join(path,folder_name,folder_name+".log")):
                recon_log_path = os.path.join(path,folder_name,folder_name+".log")
            else :
                raise Exception('No log file')

            # Check if .txt file or .log file

            # To make sure the path is in the correct format (not sure if necessary
            self.recon_log_path = os.path.abspath(recon_log_path)

            # Open the log file as read only
            recon_log_file = open(self.recon_log_path, 'r')

            # create a regex to pixel size
            prog = re.compile("^Pixel Size \(um\)\=(\w+.\w+)")

            # for loop to go through the recon log file
            for line in recon_log_file:
                # "chomp" the line endings off
                line = line.rstrip()
                # if the line matches the regex print the (\w+.\w+) part of regex
                if prog.match(line) :
                    self.pixel_size = prog.match(line).group(1)
                    break
            # Display the number on the lcd display
            self.ui.lcdNumberPixel.display(self.pixel_size)

            # Set recon log text
            self.ui.lineEditCTRecon.setText(str(self.recon_log_path))

        except IOError as e:
            self.ui.lineEditCTRecon.setText("Not found")
        except Exception as inst:
            self.ui.lineEditCTRecon.setText("Not found")
        except:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected error getting recon log file',sys.exc_info()[0])
            self.ui.lineEditCTRecon.setText("Not found")

    def autoFileOut(self):
        ''' Get info for the output file and create a new folder NEED TO ADD CREATE FOLDER FUNCTION
        '''
        try :
            input = str(self.ui.lineEditInput.text())
            # Get the folder name
            path,folder_name = os.path.split(input)
            pattern = re.compile("recons", re.IGNORECASE)
            if re.search(pattern, input):
                output_path = pattern.sub("processed recons", path)
                output_full = os.path.join(output_path,self.full_name)
                self.ui.lineEditOutput.setText(output_full)

        except:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected error getting recon log file',sys.exc_info()[0])


    def autoGetScan(self):
        input = str(self.ui.lineEditInput.text())

        # Set the scan folder
        pattern = re.compile("recons", re.IGNORECASE)
        if re.search(pattern, input):
            self.scan_folder = pattern.sub("scan", input)
            if os.path.exists(self.scan_folder):
                self.ui.lineEditScan.setText(self.scan_folder)
            else :
                self.ui.lineEditScan.setText("No found")
                self.scan_folder = ""
        else :
            self.ui.lineEditScan.setText("Not found")
            self.scan_folder = ""

    def autoGetSPR(self):
        input = str(self.ui.lineEditInput.text())
        # Get the SPR file. Sometimes fiels are saved with upper or lower case file extensions
        # The following is bit of a stupid way of dealing with this problem but I think it works....
        SPR_file_bmp = os.path.join(input,self.full_name+"_spr.bmp")
        SPR_file_BMP = os.path.join(input,self.full_name+"_spr.BMP")
        SPR_file_tif = os.path.join(input,self.full_name+"_spr.tif")
        SPR_file_TIF = os.path.join(input,self.full_name+"_spr.TIF")
        SPR_file_jpg = os.path.join(input,self.full_name+"_spr.jpg")
        SPR_file_JPG = os.path.join(input,self.full_name+"_spr.JPG")

        if os.path.isfile(SPR_file_bmp):
            self.ui.lineEditCTSPR.setText(SPR_file_bmp)
        elif os.path.isfile(SPR_file_BMP):
            self.ui.lineEditCTSPR.setText(SPR_file_BMP)
        elif os.path.isfile(SPR_file_tif):
            self.ui.lineEditCTSPR.setText(SPR_file_tif)
        elif os.path.isfile(SPR_file_TIF):
            self.ui.lineEditCTSPR.setText(SPR_file_TIF)
        elif os.path.isfile(SPR_file_jpg):
            self.ui.lineEditCTSPR.setText(SPR_file_jpg)
        elif os.path.isfile(SPR_file_JPG):
            self.ui.lineEditCTSPR.setText(SPR_file_JPG)
        else:
            self.ui.lineEditCTSPR.setText("Not found")

    def folderSizeApprox(self):
        '''
        Gets the approx folder size of the original recon folder and updates the main window with
        this information. Calculating the folder size by going through each file takes a while on janus. This
        function just checks the first recon file and then multiples this by the number of recon files.

        Updates the following qt objects: labelFile, lcdNumberFile

        Creates self.f_size_out_gb: The file size in gb
        '''

        # Get the input folder information
        input = str(self.ui.lineEditInput.text())

        # create a regex get example recon file
        prog = re.compile("(.*)_rec\d+\.(bmp|tif|jpg|jpeg)",re.IGNORECASE)

        try:
            filename = ""
            # for loop to go through the directory
            for line in os.listdir(input) :
                line =str(line)
                #print line+"\n"
                # if the line matches the regex break
                if prog.match(line) :
                    filename = line
                    break

            filename = input+"/"+filename
            file1_size = os.stat(filename).st_size

            num_files = len([f for f in os.listdir(input) if ((f[-4:] == ".bmp") or (f[-4:] == ".tif") or (f[-4:] == ".jpg") or (f[-4:] == ".jpeg") or
                          (f[-4:] == ".BMP") or (f[-4:] == ".TIF") or (f[-4:] == ".JPG") or (f[-4:] == ".JPEG") or
                          (f[-7:] != "spr.bmp") or (f[-7:] != "spr.tif") or (f[-7:] != "spr.jpg") or (f[-7:] != "spr.jpeg") or
                          (f[-7:] != "spr.BMP") or (f[-7:] != "spr.TIF") or (f[-7:] != "spr.JPG") or (f[-7:] != "spr.JPEG"))])


            approx_size = num_files*file1_size

            # convert to gb
            f_size_out =  (approx_size/(1024*1024*1024.0))

            # Save file size as an object to be used later
            self.f_size_out_gb = "%0.4f" % (f_size_out)

            #Clean up the formatting of gb mb
            self.sizeCleanup(f_size_out,approx_size)
        except:
            message = QtGui.QMessageBox.warning(self, "Message", "Unexpected error in folder size calc")
            logging.info("Unexpected error in folder size calc:", sys.exc_info()[0])



    def sizeCleanup(self,f_size_out,approx_size):
        # Check if size should be shown as gb or mb
        # Need to change file size to 2 decimal places
        if f_size_out < 0.05 :
            # convert to mb
            f_size_out =  (approx_size/(1024*1024.0))
            # make to 2 decimal places
            f_size_out =  "%0.2f" % (f_size_out)
            # change label to show mb
            self.ui.labelFile.setText("Folder size (Mb)")
            # update lcd display
            self.ui.lcdNumberFile.display(f_size_out)
        else :
            # display as gb
            # make to 2 decimal places
            f_size_out =  "%0.2f" % (f_size_out)
            # change label to show mb
            self.ui.labelFile.setText("Folder size (Gb)")
            # update lcd display
            self.ui.lcdNumberFile.display(f_size_out)



    def inputFolderChanged(self, text):
        self.inputFolder = text

    def outputFolderChanged(self, text):
        self.outputFolder = text

    def scaleByPixelOn(self):
        ''' enables boxes for scaling by pixel'''
        if self.ui.checkBoxPixel.isChecked() :
            self.ui.lineEditPixel.setEnabled(True)
        else :
            self.ui.lineEditPixel.setEnabled(False)



    def manCropOff(self):
        ''' disables boxes for cropping manually '''
        self.ui.lineEditX.setEnabled(False)
        self.ui.lineEditY.setEnabled(False)
        self.ui.lineEditW.setEnabled(False)
        self.ui.lineEditH.setEnabled(False)
        self.ui.pushButtonGetDimensions.setEnabled(False)

    def manCropOn(self):
        ''' enables boxes for cropping manually '''
        self.ui.lineEditX.setEnabled(True)
        self.ui.lineEditY.setEnabled(True)
        self.ui.lineEditW.setEnabled(True)
        self.ui.lineEditH.setEnabled(True)
        self.ui.pushButtonGetDimensions.setEnabled(True)


    def getOPTonly(self):
        ''' unchecks uCT box (if checked) and checks OPT group box and creates or edits self.modality '''
        self.ui.groupBoxOPTOnly.setChecked(True)
        self.ui.groupBoxuCTOnly.setChecked(False)
        self.modality = "OPT"

    def getuCTonly(self):
        ''' Simply unchecks OPTT box (if checked) and checks group uCT box and creates or edits self.modality '''
        self.ui.groupBoxOPTOnly.setChecked(False)
        self.ui.groupBoxuCTOnly.setChecked(True)
        self.modality = "MicroCT"

    def updateName(self):
        ''' Function to update the name of the file and folder'''
        self.full_name = str(self.ui.lineEditName.text())

        try :
            name_list = self.full_name.split("_")
            # Remove previous data
            self.ui.lineEditDate.setText("")
            self.ui.lineEditGroup.setText("")
            self.ui.lineEditAge.setText("")
            self.ui.lineEditLitter.setText("")
            self.ui.lineEditZygosity.setText("")
            self.ui.lineEditSex.setText("")

            # Add new data
            self.ui.lineEditDate.setText(name_list[0])
            self.ui.lineEditGroup.setText(name_list[1])
            self.ui.lineEditAge.setText(name_list[2])
            self.ui.lineEditLitter.setText(name_list[3])
            self.ui.lineEditZygosity.setText(name_list[4])
            self.ui.lineEditSex.setText(name_list[5])

        except IndexError as e:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Name ID is not in the correct format.\n')

        except:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected error when updating name',sys.exc_info()[0])

        # Get output folder
        output = str(self.ui.lineEditOutput.text())
        path,output_folder_name = os.path.split(output)
        self.ui.lineEditOutput.setText(os.path.join(path,self.full_name))

    def getReconMan(self):
        self.fileDialog = QtGui.QFileDialog(self)
        file = self.fileDialog.getOpenFileName()
        if not file == "":
            self.ui.lineEditCTRecon.setText(file)
            self.recon_log_path = os.path.abspath(file)

    def getScanMan(self):
        self.fileDialog = QtGui.QFileDialog(self)
        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")
        if not folder == "":
            self.ui.lineEditScan.setText(folder)#

    def getSPRMan(self):
        self.fileDialog = QtGui.QFileDialog(self)
        file= self.fileDialog.getOpenFileName()
        if not file == "":
            self.ui.lineEditCTSPR.setText(file)


    def getDimensions(self):
        ''' Perform a z projection and then allows user to crop based on z projection'''
        logging.info("########################################")
        logging.info("### Getting crop dimensions          ###")
        logging.info("########################################")

        # Opens MyMainWindow from crop.py
        input_folder = str(self.ui.lineEditInput.text())

        # Check input folder
        if not input_folder :
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input directory not defined')
            return

        if not os.path.exists(input_folder):
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not exist')
            return
        #Check if folder is empty
        elif os.listdir(input_folder) == []:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty')
            return


        zproj_path = os.path.join(str(self.tmp_dir), "z_projection")
        self.stop = None

        logging.info("Z projection is being performed")
        self.ui.textEditStatusMessages.setText("Z-projection in process, please wait")
        #Needed to update the gui
        self.app.processEvents()

        zp = zproject.Zproject(input_folder,self.tmp_dir)

        zp_result = zp.run(self.tmp_dir)

        if zp_result != 0:
            self.ui.textEditStatusMessages.setText("Z projection failed. Error message: {0}. Give Tom or Neil a Call if it happens again".format(zp_result))
            return
        logging.info("Z projection has finished")

        self.ui.textEditStatusMessages.setText("Z-projection finished")
        logging.info("Getting crop dimensions")
        self.runCrop(os.path.join(self.tmp_dir, "max_intensity_z.tif"))
        self.ui.textEditStatusMessages.setText("Dimensions selected")
        logging.info("Dimensions selected")

    def cropCallback(self, box):
        self.ui.lineEditX.setText(str(box[0]))
        self.ui.lineEditY.setText(str(box[1]))
        self.ui.lineEditW.setText(str(box[2]))
        self.ui.lineEditH.setText(str(box[3]))

    def runCrop(self, img_path):
        cropper = crop.Crop(self.cropCallback, img_path, self)
        cropper.show()


    def processGo(self):
        '''
        This will set off all the processing scripts and shows the dialog box to keep track of progress
        '''
        self.processGoSwitch = "yes"
        # Get the directory of the script
        dir = os.path.dirname(os.path.abspath(__file__))

        # Perform some checks before any processing is carried out
        self.errorCheck()

        if self.stop == None :

            self.close()

            self.getParamaters()

            # Perform analysis
            # This will run the analysi and show progress dialog window to keep track of what is being processed
            logging.basicConfig(filename=os.path.join(self.meta_path,"session.log"),level=logging.DEBUG,format='%(asctime)s %(message)s')
            self.pro = Progress(self.configOb)
            # Run the programs. A script needs to be written to run on linux to run the back end processing


    def errorCheck(self):
        '''
        To check the required inputs for the processing to be run
        '''
        # Get input and output folders (As the text is always from the text box it will hopefully keep track of
        #any changes the user might have made
        inputFolder = str(self.ui.lineEditInput.text())
        outputFolder = str(self.ui.lineEditOutput.text())

        # Check input and output folders assigned
        if not inputFolder :
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input directory not defined')
            self.stop = True
            return

        if not os.path.exists(inputFolder):
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not exist')
            self.stop = True
            return
        #Check if folder is empty
        elif os.listdir(inputFolder) == []:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty')
            self.stop = True
            return

        elif not outputFolder :
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: output directory not defined')
            self.stop = True
            return

        # Check if scan folder available if compression is required
        if self.ui.checkBoxScansReconComp.isChecked():
            if self.scan_folder == "":
                message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Scan folder not defined')
                self.stop = True
                return
            elif not os.path.exists(self.scan_folder):
                message = QtGui.QMessageBox.warning(self, 'Message', "Warning: Scan folder does not exist")
                self.stop = True
                return



        # Check pixel size is a number
        if self.ui.checkBoxPixel.isChecked() :

            try:
                testing = float(self.ui.lineEditPixel.text())
            except ValueError:
                if not self.ui.lineEditPixel.text():
                    message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: User has not specified a new pixel size value')
                else :
                    message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: User defined pixel is not a numerical value')
                self.stop = True
                return

        # Check user has not selected to scale by pixel without having a recon folder
        if self.ui.checkBoxPixel.isChecked() and self.pixel_size == "" :
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Pixel size could not be obtained from original recon log. Scaling "By Pixel (um) is not possible')
            return

        # Check cropping parameters ok
        if self.ui.radioButtonMan.isChecked() :
            try:
                testing = float(self.ui.lineEditX.text())
                testing = float(self.ui.lineEditY.text())
                testing = float(self.ui.lineEditW.text())
                testing = float(self.ui.lineEditH.text())
            except ValueError:
                message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Cropping dimensions have not been defined')
                self.stop = True
                return

        # Check input directory contains something
        if os.listdir(inputFolder) == []:
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty, please check')
            self.stop = True
            return


        # Input folder contains image files
        if self.ui.checkBoxRF.isChecked():
            # Too dangerous to delete everything in a folder
            # shutil.rmtree(outputFolder)
            # os.makedirs(outputFolder)
            self.stop = None
        # Check if output folder already exists. Ask if it is ok to overwrite
        elif os.path.exists(outputFolder):
            # Running dialog box to inform user of options
            message = QtGui.QMessageBox.question(self, 'Message', 'Folder already exists for the location:\n{0}\nCan this folder be overwritten?'.format(outputFolder) , QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if message == QtGui.QMessageBox.Yes:
                self.stop = None
            if message == QtGui.QMessageBox.No:
                self.stop = True
            return
        else :
            logging.info("Creating output folder")
            os.makedirs(outputFolder)
            self.stop = None




    def getParamaters(self):
        '''
        Creates the config file for future processing
        '''
        # Get input and output folders (As the text is always from the text box it will hopefully keep track of
        #any changes the user might have made
        inputFolder = str(self.ui.lineEditInput.text())
        outputFolder = str(self.ui.lineEditOutput.text())

        #### Write to config file ####
        self.configOb = ConfigClass()

        # Create a folder for the metadata
        self.meta_path = os.path.join(outputFolder,"Metadata")
        if not os.path.exists(self.meta_path):
            os.makedirs(self.meta_path)

        # OS path used for compatibility issues between Linux and windows directory spacing
        self.config_path = os.path.join(self.meta_path,"configObject.txt")
        self.log_path = os.path.join(self.meta_path,"config4user.log")

        # Create config file and log file
        config = open(self.config_path, 'w')
        log = open(self.log_path, 'w')

        #######################################
        # Create config object                #
        #######################################
        # Get cropping options
        if self.ui.radioButtonMan.isChecked() :
            self.configOb.xcrop = str(self.ui.lineEditX.text())
            self.configOb.ycrop = str(self.ui.lineEditY.text())
            self.configOb.wcrop = str(self.ui.lineEditW.text())
            self.configOb.hcrop = str(self.ui.lineEditH.text())
            self.configOb.crop_option = "Manual"
            self.configOb.crop_manual = self.configOb.xcrop+" "+self.configOb.ycrop+" "+self.configOb.wcrop+" "+self.configOb.hcrop
        elif self.ui.radioButtonAuto.isChecked() :
            self.configOb.crop_manual = "Not_applicable"
            self.configOb.crop_option = "Automatic"
        elif self.ui.radioButtonNo.isChecked() :
            self.configOb.crop_manual = "Not_applicable"
            self.configOb.crop_option = "No_crop"

        ##### Get Scaling factors ####
        if self.ui.checkBoxSF2.isChecked() :
            self.configOb.SF2 = "yes"
        else :
            self.configOb.SF2 = "no"

        if self.ui.checkBoxSF3.isChecked() :
            self.configOb.SF3 = "yes"
        else :
            self.configOb.SF3 = "no"

        if self.ui.checkBoxSF4.isChecked() :
            self.configOb.SF4 = "yes"
        else :
            self.configOb.SF4 = "no"

        if self.ui.checkBoxSF5.isChecked() :
            self.configOb.SF5 = "yes"
        else :
            self.configOb.SF5 = "no"

        if self.ui.checkBoxSF6.isChecked() :
            self.configOb.SF6 = "yes"
        else :
            self.configOb.SF6 = "no"

        if self.ui.checkBoxPixel.isChecked() :
            self.configOb.pixel_option = "yes"
            self.configOb.user_specified_pixel = str(self.ui.lineEditPixel.text())
            self.configOb.SF_pixel = float(self.pixel_size) / float(self.ui.lineEditPixel.text())
            self.configOb.SF_pixel = round(self.configOb.SF_pixel,4)
            self.configOb.SFX_pixel = float(self.ui.lineEditPixel.text())/float(self.pixel_size)
            self.configOb.SFX_pixel = round(self.configOb.SFX_pixel,4)
        else :
            self.configOb.user_specified_pixel = "Not applicable"
            self.configOb.pixel_option = "no"
            self.configOb.SF_pixel = "Not applicable"
            self.configOb.SFX_pixel = "Not applicable"

        if self.ui.checkBoxScansReconComp.isChecked():
            self.configOb.scans_recon_comp = "yes"
        else :
            self.configOb.scans_recon_comp = "No"

        if self.ui.checkBoxCropComp.isChecked():
            self.configOb.crop_comp = "yes"
        else :
            self.configOb.crop_comp  = "No"

        # ID for session
        self.configOb.unique_ID = str(self.unique_ID)
        self.configOb.config_path = self.config_path
        self.configOb.tmp_dir = self.tmp_dir
        self.configOb.full_name = self.full_name
        self.configOb.input_folder = inputFolder
        self.configOb.output_folder = outputFolder
        self.configOb.scan_folder = self.scan_folder
        self.configOb.meta_path = self.meta_path
        self.configOb.recon_log_file = self.recon_log_path
        self.configOb.recon_folder_size = self.f_size_out_gb
        self.configOb.recon_pixel_size = self.pixel_size

        # If using windows it is important to put \ at the end of folder name
        # Combining scaling and SF into input for imageJ macro
        self.configOb.cropped_path = os.path.join(self.configOb.output_folder,"cropped")
        self.configOb.scale_path = os.path.join(self.configOb.output_folder,"scaled_stacks")
        if self.configOb.crop_option == "No_crop":
            self.configOb.imageJ = self.configOb.input_folder+os.sep+'^'+self.configOb.scale_path+os.sep+'^'+self.configOb.full_name
        else :
            self.configOb.imageJ = self.configOb.cropped_path+os.sep+'^'+self.configOb.scale_path+os.sep+'^'+self.configOb.full_name

        # write the config information into an easily readable log file
        log.write("Session_ID    "+self.configOb.unique_ID+"\n");
        log.write("full_name    "+self.configOb.full_name+"\n");
        log.write("Input_folder    "+self.configOb.input_folder+"\n");
        log.write("Output_folder    "+self.configOb.output_folder+"\n");
        log.write("Scan_folder    "+self.configOb.scan_folder+"\n");
        log.write("Crop_option    "+self.configOb.crop_option+"\n");
        log.write("Crop_manual    "+self.configOb.crop_manual+"\n");
        log.write("Downsize_by_factor_2?    "+self.configOb.SF2+"\n");
        log.write("Downsize_by_factor_3?    "+self.configOb.SF3+"\n");
        log.write("Downsize_by_factor_4?    "+self.configOb.SF4+"\n");
        log.write("Downsize_by_factor_5?    "+self.configOb.SF4+"\n");
        log.write("Downsize_by_factor_6?    "+self.configOb.SF4+"\n");
        log.write("Downsize_by_pixel?    "+self.configOb.pixel_option+"\n");
        log.write("User_specified_pixel_size?    "+self.configOb.user_specified_pixel+"\n");
        log.write("Downsize_value_for_pixel    "+str(self.configOb.SF_pixel)+"\n");
        log.write("Compression_of_scans_and_original_recon?    "+self.configOb.scans_recon_comp+"\n");
        log.write("Compression_of_cropped_recon?    "+self.configOb.crop_comp+"\n");
        log.write("ImageJconfig    "+self.configOb.imageJ+"\n");
        log.write("Recon_log_file    "+self.configOb.recon_log_file+"\n");
        log.write("Recon_folder_size   "+self.configOb.recon_folder_size+"\n");
        log.write("Recon_pixel_size  "+self.configOb.recon_pixel_size+"\n");

        # Pickle the class to a file
        pickle.dump(self.configOb, config)

        config.close()
        log.close()


class ConfigClass :
    '''
    A simple Class is used to transfer config information
    '''
    def __init__(self):

        logging.info("ConfigClass init")


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow(app)
    sys.exit(app.exec_())


if __name__ == "__main__":
    freeze_support()
    main()